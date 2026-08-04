from __future__ import annotations

import io
from itertools import pairwise
from pathlib import Path

import h5py
import numpy as np
import pytest
import torch

from bubbleml_benchmark.data import (
    ChannelNormalizer,
    PreprocessConfig,
    TensorSampleDataset,
    preprocess_hdf5,
)
from bubbleml_benchmark.hybrid_analysis import (
    PREDECLARED_TESTS,
    _one_sided_sign_flip_pvalue,
    analyze,
)
from bubbleml_benchmark.divergence_analysis import analyze as analyze_divergence
from bubbleml_benchmark.paper_models import PaperModelSpec, build_paper_model
from bubbleml_benchmark.paper_train import (
    PaperTrainingConfig,
    _resize,
    _tensor_state_dict,
    spectral_divergence_mae,
)
from bubbleml_benchmark.temporal import TemporalBundleDataset
from bubbleml_benchmark.lambda_sensitivity import analyze as analyze_lambda_sensitivity
from bubbleml_benchmark.paper_figures import bootstrap_mean_interval, paired_model_intervals
from bubbleml_benchmark.refresh_paper_statistics import refresh as refresh_paper_statistics


def _write_trajectory(path: Path, offset: float) -> None:
    time, height, width = 16, 9, 11
    y, x = np.mgrid[:height, :width].astype(np.float32)
    steps = np.arange(time, dtype=np.float32)[:, None, None]
    base = offset + steps + x[None] * 0.01 + y[None] * 0.02
    with h5py.File(path, "w") as handle:
        handle["temperature"] = base
        handle["velx"] = base * 0.1
        handle["vely"] = base * 0.2
        handle["pressure"] = base * 0.3
        handle["dfun"] = x[None] - width / 2 + 0.1 * steps
        handle["x"] = np.broadcast_to(x, (time, height, width)).copy()
        handle["y"] = np.broadcast_to(y, (time, height, width)).copy()


def _prepared_dataset(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    raw.mkdir()
    for index in range(3):
        _write_trajectory(raw / f"trajectory_{index}.hdf5", float(index))
    output = tmp_path / "pt"
    preprocess_hdf5(
        PreprocessConfig(
            input_dir=str(raw),
            output_dir=str(output),
            start_step=0,
            rollout_steps=1,
            val_fraction=0.34,
            test_fraction=0.34,
            split_seed=42,
        )
    )
    return output


def test_temporal_bundle_is_five_field_and_trajectory_safe(tmp_path: Path) -> None:
    output = _prepared_dataset(tmp_path)
    raw_train = TensorSampleDataset(output, split="train")
    normalizer = ChannelNormalizer.fit(raw_train)
    dataset = TemporalBundleDataset(
        output,
        "train",
        normalizer,
        history_size=3,
        future_size=2,
        rollout_bundles=2,
    )
    sample = dataset[0]
    assert dataset.channel_names == (
        "u",
        "v",
        "pressure_gradient",
        "temperature",
        "alpha_vapor_mask",
    )
    assert sample["input"].shape == (15, 9, 11)
    assert sample["target"].shape == (10, 9, 11)
    assert sample["rollout_targets"].shape == (2, 10, 9, 11)
    assert dataset.decode_frames(sample["target"], 2).shape == (2, 5, 9, 11)
    first_window = dataset.windows[0]
    sources = {dataset.base.entries[index]["source"] for index in first_window}
    timesteps = [int(dataset.base.entries[index]["timestep"]) for index in first_window]
    assert len(sources) == 1
    assert all(right - left == 1 for left, right in pairwise(timesteps))


def test_cached_temporal_bundle_matches_uncached(tmp_path: Path) -> None:
    output = _prepared_dataset(tmp_path)
    normalizer = ChannelNormalizer.fit(TensorSampleDataset(output, split="train"))
    kwargs = {"history_size": 3, "future_size": 2, "rollout_bundles": 1}
    uncached = TemporalBundleDataset(output, "train", normalizer, **kwargs)
    cached = TemporalBundleDataset(output, "train", normalizer, cache_frames=True, **kwargs)
    assert cached._encoded_cache
    assert torch.equal(cached[0]["input"], uncached[0]["input"])
    assert torch.equal(cached[0]["target"], uncached[0]["target"])


@pytest.mark.parametrize(
    "kind", ["fno", "tfno", "hybrid_tfno", "hybrid_div", "ffno", "unet"]
)
def test_paper_models_preserve_odd_spatial_shape(kind: str) -> None:
    spec = PaperModelSpec(
        kind=kind,  # type: ignore[arg-type]
        in_channels=15,
        out_channels=10,
        requested_modes=(64, 64),
        effective_modes=(4, 4),
        width=8,
        layers=2,
        unet_features=8,
        unet_depth=3,
    )
    inputs = torch.randn(1, 15, 17, 19)
    outputs = build_paper_model(spec)(inputs)
    assert outputs.shape == (1, 10, 17, 19)


def test_tfno_has_fewer_real_scalar_parameters_than_dense_fno() -> None:
    common = {
        "in_channels": 15,
        "out_channels": 10,
        "requested_modes": (8, 8),
        "effective_modes": (8, 8),
        "width": 16,
        "layers": 2,
    }
    dense = build_paper_model(PaperModelSpec(kind="fno", **common))
    tucker = build_paper_model(PaperModelSpec(kind="tfno", tfno_rank=0.1, **common))
    dense_parameters = sum(
        parameter.numel() * (2 if parameter.is_complex() else 1) for parameter in dense.parameters()
    )
    tucker_parameters = sum(
        parameter.numel() * (2 if parameter.is_complex() else 1)
        for parameter in tucker.parameters()
    )
    assert tucker_parameters < dense_parameters


def test_hybrid_tfno_adds_one_local_branch_per_spectral_layer() -> None:
    spec = PaperModelSpec(
        kind="hybrid_tfno",
        in_channels=15,
        out_channels=10,
        effective_modes=(4, 4),
        width=8,
        layers=3,
    )
    model = build_paper_model(spec)
    assert len(model.fno_blocks.local_convs) == 3  # type: ignore[attr-defined]
    assert all(
        layer.kernel_size == (3, 3)
        for layer in model.fno_blocks.local_convs  # type: ignore[attr-defined]
    )
    payload = {"model_state_dict": _tensor_state_dict(model)}
    stream = io.BytesIO()
    torch.save(payload, stream)
    stream.seek(0)
    restored = torch.load(stream, map_location="cpu", weights_only=True)
    build_paper_model(spec).load_state_dict(restored["model_state_dict"], strict=True)


def test_fourier_resize_accepts_batched_and_unbatched_fields() -> None:
    assert _resize(torch.zeros(15, 10, 14), 2).shape == (15, 5, 7)
    assert _resize(torch.zeros(2, 15, 10, 14), 2).shape == (2, 15, 5, 7)


def test_fno_state_is_weights_only_safe() -> None:
    spec = PaperModelSpec(
        kind="fno",
        in_channels=15,
        out_channels=10,
        effective_modes=(4, 4),
        width=8,
        layers=2,
    )
    payload = {"model_state_dict": _tensor_state_dict(build_paper_model(spec))}
    stream = io.BytesIO()
    torch.save(payload, stream)
    stream.seek(0)
    restored = torch.load(stream, map_location="cpu", weights_only=True)
    model = build_paper_model(spec)
    model.load_state_dict(restored["model_state_dict"], strict=True)


def test_bounded_alpha_output_maps_only_alpha_to_physical_unit_interval() -> None:
    mean = 0.3
    std = 0.2
    spec = PaperModelSpec(
        kind="unet",
        in_channels=5,
        out_channels=10,
        unet_features=4,
        unet_depth=2,
        alpha_bounded=True,
        alpha_output_indices=(4, 9),
        alpha_normalized_lower=-mean / std,
        alpha_normalized_upper=(1.0 - mean) / std,
    )
    output = build_paper_model(spec)(torch.randn(2, 5, 8, 8))
    decoded_alpha = output[:, (4, 9)] * std + mean
    assert float(decoded_alpha.detach().min()) >= 0.0
    assert float(decoded_alpha.detach().max()) <= 1.0
    assert output[:, (0, 1, 2, 3, 5, 6, 7, 8)].isfinite().all()

    restored = PaperModelSpec.from_state_dict(spec.state_dict())
    assert restored == spec


def test_gpu_run_defaults_use_full_resolution_and_valid_48_grid_modes() -> None:
    config = PaperTrainingConfig(data_dir="unused")
    assert config.fourier_downsample_factor == 1
    assert config.requested_modes == 24
    assert config.max_epochs == 200
    assert config.max_minutes_per_run == 0.0
    assert config.plateau_window == 5
    assert config.seeds == (42, 100, 1234, 2025, 9999)


def test_hybrid_noninferiority_analysis_uses_one_holm_family() -> None:
    raw: dict[str, dict[int, dict[str, float]]] = {
        kind: {seed: {} for seed in range(11)}
        for kind in ("hybrid_tfno", "tfno", "unet")
    }
    for test in PREDECLARED_TESTS:
        metric = str(test["metric"])
        comparator = str(test["comparator"])
        for seed in range(11):
            raw["hybrid_tfno"][seed][metric] = 0.9
            raw[comparator][seed][metric] = 1.0
    result = analyze({"raw_seed_metrics": raw}, bootstrap_samples=100)
    assert result["pareto_break"] is True
    assert len(result["tests"]) == 3
    assert all(row["holm_noninferiority_p"] < 0.05 for row in result["tests"].values())


def test_spectral_divergence_is_zero_for_cross_axis_periodic_velocity() -> None:
    height = width = 16
    y = torch.arange(height, dtype=torch.float32).view(height, 1) / height
    x = torch.arange(width, dtype=torch.float32).view(1, width) / width
    u = torch.sin(2 * torch.pi * y).expand(height, width)
    v = torch.cos(2 * torch.pi * x).expand(height, width)
    prediction = torch.stack((u, v, torch.zeros_like(u), torch.zeros_like(u), torch.zeros_like(u)))
    normalizer = ChannelNormalizer(
        torch.zeros(5),
        torch.ones(5),
        ("u", "v", "pressure_gradient", "temperature", "alpha_vapor_mask"),
    )
    value = spectral_divergence_mae(
        prediction.unsqueeze(0),
        normalizer,
        normalizer.channel_names,
        future_size=1,
        dx=torch.tensor([1.0 / width]),
        dy=torch.tensor([1.0 / height]),
    )
    assert float(value) < 1e-5


def test_spectral_divergence_backpropagates_to_velocity_channels() -> None:
    prediction = torch.randn(2, 10, 8, 8, requires_grad=True)
    normalizer = ChannelNormalizer(
        torch.zeros(5),
        torch.ones(5),
        ("u", "v", "pressure_gradient", "temperature", "alpha_vapor_mask"),
    )
    loss = spectral_divergence_mae(
        prediction,
        normalizer,
        normalizer.channel_names,
        future_size=2,
        dx=torch.ones(2),
        dy=torch.ones(2),
    )
    loss.backward()
    assert prediction.grad is not None
    assert float(prediction.grad[:, (0, 1, 5, 6)].abs().sum()) > 0
    assert float(prediction.grad[:, (2, 3, 4, 7, 8, 9)].abs().sum()) == 0


def test_divergence_confirmation_requires_and_accepts_eleven_paired_seeds() -> None:
    raw = {
        "hybrid_div": {
            seed: {"mass_conservation_mae": 0.1} for seed in range(11)
        },
        "unet": {seed: {"mass_conservation_mae": 0.1} for seed in range(11)},
    }
    result = analyze_divergence({"raw_seed_metrics": raw}, bootstrap_samples=100)
    assert result["result"]["n_seeds"] == 11
    assert result["result"]["noninferior"] is True


def test_exact_one_sided_sign_flip_has_eleven_seed_minimum() -> None:
    assert _one_sided_sign_flip_pvalue(-np.ones(11)) == pytest.approx(1 / 2048)


def test_lambda_sensitivity_uses_paired_three_seed_guards() -> None:
    seeds = (42, 100, 1234)
    def payload(model: str, mse: float, divergence: float, interface: float) -> dict:
        return {
            "models": {
                model: {
                    str(seed): {
                        "validation_mse": mse + seed * 1e-8,
                        "validation_spectral_divergence_mae": divergence,
                        "validation_interface_temperature_rmse": interface,
                    }
                    for seed in seeds
                }
            }
        }

    result = analyze_lambda_sensitivity(
        payload("hybrid_tfno", 1.0, 1.0, 2.0),
        {
            0.1: payload("hybrid_div", 1.01, 0.8, 2.01),
            0.2: payload("hybrid_div", 1.02, 0.6, 2.04),
            0.3: payload("hybrid_div", 1.02, 0.4, 2.20),
        },
        bootstrap_samples=100,
    )
    assert result["selected_lambda_div"] == pytest.approx(0.2)
    assert result["selected_is_interior"] is True
    assert result["candidates"]["0.3"]["eligible"] is False


def test_figure_bootstrap_interval_is_deterministic() -> None:
    first = bootstrap_mean_interval([1.0, 2.0, 3.0], samples=100, seed=7)
    second = bootstrap_mean_interval([1.0, 2.0, 3.0], samples=100, seed=7)
    assert first == second
    assert first[0] <= 2.0 <= first[1]


def test_pareto_intervals_share_the_paired_seed_resample() -> None:
    raw = {
        "tfno": {str(seed): {"metric": value} for seed, value in enumerate((1.0, 2.0, 5.0))},
        "unet": {
            str(seed): {"metric": value + 10.0}
            for seed, value in enumerate((1.0, 2.0, 5.0))
        },
    }
    intervals = paired_model_intervals(
        raw, "metric", ("tfno", "unet"), samples=200, seed=9
    )
    assert intervals["unet"][0] == pytest.approx(intervals["tfno"][0] + 10.0)
    assert intervals["unet"][1] == pytest.approx(intervals["tfno"][1] + 10.0)


def test_paper_statistics_can_be_refreshed_without_model_evaluation() -> None:
    rows = {
        "tfno": {str(seed): {"gwrmse": 2.0} for seed in range(5)},
        "unet": {str(seed): {"gwrmse": 1.0} for seed in range(5)},
        "hybrid_tfno": {str(seed): {"gwrmse": 1.5} for seed in range(5)},
        "hybrid_div": {str(seed): {"gwrmse": 1.25} for seed in range(5)},
    }
    refreshed = refresh_paper_statistics({"raw_seed_metrics": rows}, bootstrap_samples=100)
    assert refreshed["pairwise_model_minus_unet"]["tfno"]["gwrmse"][
        "paired_sign_flip_p"
    ] == pytest.approx(0.0625)
    assert "hybrid_div" in refreshed["pairwise_model_minus_hybrid_tfno"]
