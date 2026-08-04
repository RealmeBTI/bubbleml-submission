from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
import pytest
import torch

from bubbleml_benchmark.benchmark import _paired_sign_flip_pvalue, paired_comparison
from bubbleml_benchmark.data import (
    ChannelNormalizer,
    DatasetValidationError,
    PreprocessConfig,
    TensorSampleDataset,
    preprocess_hdf5,
)
from bubbleml_benchmark.metrics import sample_metrics
from bubbleml_benchmark.models import ModelSpec, build_model


def _write_trajectory(path: Path, offset: float) -> None:
    time, height, width = 6, 9, 11
    y, x = np.mgrid[:height, :width].astype(np.float32)
    with h5py.File(path, "w") as handle:
        base = np.stack([offset + step + x * 0.01 + y * 0.02 for step in range(time)]).astype(np.float32)
        handle["temperature"] = base
        handle["velx"] = base * 0.1
        handle["vely"] = base * 0.2
        handle["pressure"] = base * 0.3
        handle["dfun"] = x[None] - (width / 2) + 0.1 * np.arange(time)[:, None, None]
        handle["x"] = np.broadcast_to(x, (time, height, width)).copy()
        handle["y"] = np.broadcast_to(y, (time, height, width)).copy()


def test_preprocess_real_hdf5_schema_and_normalization(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for index in range(3):
        _write_trajectory(raw / f"trajectory_{index}.hdf5", float(index))
    output = tmp_path / "pt"
    manifest = preprocess_hdf5(
        PreprocessConfig(
            input_dir=str(raw),
            output_dir=str(output),
            start_step=0,
            rollout_steps=2,
            val_fraction=0.34,
            test_fraction=0.34,
        )
    )
    assert manifest["channel_names"] == ["u", "v", "pressure_gradient", "temperature", "alpha_vapor_mask"]
    assert {sample["split"] for sample in manifest["samples"]} == {"train", "val", "test"}
    raw_train = TensorSampleDataset(output, split="train")
    normalizer = ChannelNormalizer.fit(raw_train)
    train = TensorSampleDataset(output, split="train", normalizer=normalizer)
    sample = train[0]
    assert sample["input"].shape == (5, 9, 11)
    assert sample["rollout_targets"].shape == (2, 5, 9, 11)
    assert sample["dx"] == pytest.approx(1.0)
    assert sample["dy"] == pytest.approx(1.0)
    assert normalizer.decode(sample["input"]).shape == sample["input"].shape


def test_dataset_fails_without_manifest(tmp_path: Path) -> None:
    with pytest.raises(DatasetValidationError, match="manifest"):
        TensorSampleDataset(tmp_path)


def test_preprocess_explicit_split_and_downsample(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for index in range(4):
        _write_trajectory(raw / f"trajectory_{index}.hdf5", float(index))
    output = tmp_path / "pt"
    manifest = preprocess_hdf5(
        PreprocessConfig(
            input_dir=str(raw),
            output_dir=str(output),
            start_step=0,
            target_resolution=5,
            train_sources=("trajectory_0",),
            val_sources=("trajectory_1.hdf5",),
            test_sources=("trajectory_3",),
        )
    )
    assert len(manifest["excluded_source_files"]) == 1
    assert {Path(row["source"]).stem for row in manifest["samples"]} == {
        "trajectory_0",
        "trajectory_1",
        "trajectory_3",
    }
    train = TensorSampleDataset(output, split="train")
    sample = train.raw_item(0)
    assert sample["input"].shape == (5, 5, 5)
    assert set(torch.unique(sample["input"][-1]).tolist()).issubset({0.0, 1.0})
    assert sample["dx"] == pytest.approx(11 / 5)
    assert sample["dy"] == pytest.approx(9 / 5)


def test_preprocess_balanced_per_source_cap(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for index in range(3):
        _write_trajectory(raw / f"trajectory_{index}.hdf5", float(index))
    output = tmp_path / "pt"
    manifest = preprocess_hdf5(
        PreprocessConfig(
            input_dir=str(raw),
            output_dir=str(output),
            start_step=0,
            max_samples_per_source=2,
            train_sources=("trajectory_0",),
            val_sources=("trajectory_1",),
            test_sources=("trajectory_2",),
        )
    )
    counts = {
        split: sum(row["split"] == split for row in manifest["samples"])
        for split in ("train", "val", "test")
    }
    assert counts == {"train": 2, "val": 2, "test": 2}


@pytest.mark.parametrize("kind", ["fno", "unet"])
def test_models_preserve_non_multiple_spatial_shape(kind: str) -> None:
    spec = ModelSpec(
        kind=kind,  # type: ignore[arg-type]
        in_channels=4,
        out_channels=4,
        fno_modes=(4, 4),
        fno_width=8,
        fno_layers=2,
        unet_features=8,
        unet_depth=3,
    )
    inputs = torch.randn(1, 4, 17, 19)
    outputs = build_model(spec)(inputs)
    assert outputs.shape == inputs.shape


def test_interface_metrics_are_defined_for_a_2d_alpha_mask() -> None:
    target = torch.zeros(4, 9, 11)
    target[2, 3:6, 3:7] = 1.0
    target[3, :, 5:] = 1.0
    prediction = target + 0.1
    metrics = sample_metrics(prediction, target, ("u", "v", "temperature", "alpha_vapor_mask"), 1.0, 1.0)
    assert metrics["interface_alpha_rmse"] is not None
    assert metrics["interface_temperature_jump_mae"] is not None
    assert metrics["gwrmse"] is not None


def test_single_seed_statistics_are_json_safe() -> None:
    raw = {
        "fno": {42: {"gwrmse": 2.0, "parameters": 1.0}},
        "unet": {42: {"gwrmse": 1.0, "parameters": 1.0}},
    }
    result = paired_comparison(raw, bootstrap_samples=10)
    assert result["gwrmse"]["ci95_low"] is None
    assert json.loads(json.dumps(result))["gwrmse"]["ci95_high"] is None


def test_compute_descriptors_are_excluded_from_paired_error_family() -> None:
    compute = {
        "parameters": 1.0,
        "real_scalar_parameters": 2.0,
        "throughput_fps": 3.0,
        "throughput_windows_per_second": 4.0,
        "latency_ms_per_sample": 5.0,
        "latency_ms_per_window": 6.0,
        "model_inference_latency_ms_per_window": 7.0,
        "model_inference_throughput_windows_per_second": 8.0,
    }
    raw = {
        "fno": {42: {"gwrmse": 2.0, **compute}, 100: {"gwrmse": 3.0, **compute}},
        "unet": {42: {"gwrmse": 1.0, **compute}, 100: {"gwrmse": 1.5, **compute}},
    }
    result = paired_comparison(raw, bootstrap_samples=10)
    assert set(result) == {"gwrmse"}


def test_exact_two_sided_sign_flip_has_five_seed_minimum() -> None:
    assert _paired_sign_flip_pvalue(np.ones(5)) == pytest.approx(2 / 32)
