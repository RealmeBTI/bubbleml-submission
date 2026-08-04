"""Fail-closed evaluation, paired inference, and statistics for BubbleML baselines."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

from .data import ChannelNormalizer, DatasetValidationError, TensorSampleDataset
from .metrics import MetricAccumulator, gradient_weighted_rmse, sample_metrics
from .models import ModelSpec, build_model
from .runtime import (
    autocast_enabled,
    available_device,
    device_autocast,
    fno_device,
    set_seed,
    synchronize,
)
from .train import DEFAULT_SEEDS


@dataclass(frozen=True)
class BenchmarkConfig:
    data_dir: str
    checkpoints_dir: str = "checkpoints"
    output_dir: str = "benchmark_results"
    seeds: tuple[int, ...] = DEFAULT_SEEDS
    batch_size: int = 2
    num_workers: int = 0
    device: str = "auto"
    fno_device: str = "auto"
    use_amp: bool = False
    warmup_batches: int = 2
    rollout_steps: int = 1
    bootstrap_samples: int = 10_000


def _safe_load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required checkpoint is absent: {path}. Train it first; untrained weights are never benchmarked."
        )
    try:
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError as exc:  # pragma: no cover - project requires torch >= 2.2
        raise RuntimeError("BubbleML benchmark requires PyTorch >= 2.2.") from exc
    required = {"model_kind", "seed", "model_spec", "model_state_dict", "normalizer", "channel_names"}
    missing = required.difference(checkpoint)
    if missing:
        raise DatasetValidationError(f"{path} is not a BubbleML benchmark checkpoint; missing {sorted(missing)}.")
    return checkpoint


def _loader(dataset: TensorSampleDataset, config: BenchmarkConfig) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=False,
        persistent_workers=config.num_workers > 0,
    )


def _checkpoint_path(root: Path, kind: str, seed: int) -> Path:
    return root / f"{kind}_seed_{seed}.pt"


@torch.inference_mode()
def evaluate_checkpoint(
    checkpoint: Mapping[str, Any],
    dataset_root: str,
    config: BenchmarkConfig,
    kind: str,
) -> dict[str, float]:
    spec = ModelSpec.from_state_dict(checkpoint["model_spec"])
    if spec.kind != kind or checkpoint["model_kind"] != kind:
        raise DatasetValidationError(f"Checkpoint model kind does not match requested {kind} evaluation.")
    normalizer = ChannelNormalizer.from_state_dict(checkpoint["normalizer"])
    dataset = TensorSampleDataset(dataset_root, split="test", normalizer=normalizer)
    if tuple(checkpoint["channel_names"]) != dataset.channel_names:
        raise DatasetValidationError("Checkpoint channel schema differs from held-out test manifest.")
    loader = _loader(dataset, config)
    if kind == "fno":
        requested = config.fno_device if config.fno_device != "auto" else config.device
        device = fno_device(requested, spec, sample_shape=dataset[0]["input"].shape[-2:])
    else:
        device = available_device(config.device)
    model = build_model(spec)
    incompatible = model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:  # strict=True normally raises; retain a clear guard.
        raise DatasetValidationError("Checkpoint state dict does not exactly match the declared model specification.")
    model = model.to(device).eval()
    amp = autocast_enabled(device, config.use_amp, spec.kind)

    for warmups, batch in enumerate(loader, start=1):
        inputs = batch["input"].to(device, non_blocking=device.type == "cuda")
        with device_autocast(device, amp):
            _ = model(inputs)
        if warmups >= config.warmup_batches:
            break
    synchronize(device)
    start = time.perf_counter()
    metrics = MetricAccumulator()
    rollout_relative_l2 = MetricAccumulator()
    examples = 0
    for batch in loader:
        inputs = batch["input"].to(device, non_blocking=device.type == "cuda")
        targets = batch["target"].to(device, non_blocking=device.type == "cuda")
        with device_autocast(device, amp):
            predictions = model(inputs)
        physical_predictions = normalizer.decode(predictions.float())
        physical_targets = normalizer.decode(targets.float())
        for index in range(inputs.shape[0]):
            values = sample_metrics(
                physical_predictions[index],
                physical_targets[index],
                dataset.channel_names,
                float(batch["dx"][index]),
                float(batch["dy"][index]),
            )
            metrics.update(values)
        # True autoregressive error is only defined if the preprocessor stored
        # all requested future frames.  It is not inferred from predictions.
        available_rollout = int(batch["rollout_targets"].shape[1])
        steps = min(config.rollout_steps, available_rollout)
        if steps:
            current = inputs
            normalized_rollout_targets = batch["rollout_targets"][:, :steps].to(device)
            for step in range(steps):
                with device_autocast(device, amp):
                    current = model(current)
                physical_current = normalizer.decode(current.float())
                physical_future = normalizer.decode(normalized_rollout_targets[:, step].float())
                per_sample = (physical_current - physical_future).flatten(1).norm(dim=1) / physical_future.flatten(1).norm(dim=1).clamp_min(1e-8)
                alpha_index = dataset.channel_names.index("alpha_vapor_mask")
                alpha_gwrmse = gradient_weighted_rmse(
                    physical_current[:, alpha_index : alpha_index + 1],
                    physical_future[:, alpha_index : alpha_index + 1],
                )
                for value, alpha_value in zip(per_sample, alpha_gwrmse, strict=True):
                    rollout_relative_l2.update(
                        {"rollout_relative_l2": float(value.item()), "rollout_alpha_gwrmse": float(alpha_value.item())}
                    )
        examples += int(inputs.shape[0])
    synchronize(device)
    elapsed = time.perf_counter() - start
    if not examples:
        raise RuntimeError("Benchmark DataLoader yielded no test samples.")
    result = metrics.mean()
    result.update(rollout_relative_l2.mean())
    result["throughput_fps"] = examples / elapsed
    result["latency_ms_per_sample"] = 1_000.0 * elapsed / examples
    result["parameters"] = float(sum(parameter.numel() for parameter in model.parameters()))
    # Complex FNO coefficients represent two real scalars each.  Report the
    # real-scalar equivalent alongside regular PyTorch parameter count.
    result["real_scalar_parameters"] = float(
        sum(parameter.numel() * (2 if parameter.is_complex() else 1) for parameter in model.parameters())
    )
    result["device"] = str(device)
    return result


def _bootstrap_ci(values: np.ndarray, samples: int, seed: int = 0) -> tuple[float | None, float | None]:
    if len(values) < 2:
        return (None, None)
    rng = np.random.default_rng(seed)
    means = rng.choice(values, size=(samples, len(values)), replace=True).mean(axis=1)
    return tuple(float(value) for value in np.quantile(means, (0.025, 0.975)))


def _paired_sign_flip_pvalue(differences: np.ndarray) -> float:
    """Exact two-sided paired randomization p-value for up to 20 seeds."""
    if len(differences) == 0 or np.allclose(differences, 0):
        return 1.0
    observed = abs(float(differences.mean()))
    if len(differences) > 20:
        rng = np.random.default_rng(0)
        signs = rng.choice((-1.0, 1.0), size=(100_000, len(differences)))
        distribution = np.abs((signs * differences).mean(axis=1))
        return float((np.count_nonzero(distribution >= observed) + 1) / (len(distribution) + 1))
    else:
        distribution = np.fromiter(
            (abs(float((np.asarray(signs) * differences).mean())) for signs in itertools.product((-1.0, 1.0), repeat=len(differences))),
            dtype=float,
        )
        return float(np.count_nonzero(distribution >= observed) / len(distribution))


def paired_comparison(
    raw: Mapping[str, Mapping[int, Mapping[str, float]]], bootstrap_samples: int
) -> dict[str, dict[str, float | None]]:
    if set(raw) != {"fno", "unet"}:
        return {}
    common_seeds = sorted(set(raw["fno"]).intersection(raw["unet"]))
    if not common_seeds:
        return {}
    metric_names = sorted(
        set.intersection(
            *(set(raw[model][seed]) for model in ("fno", "unet") for seed in common_seeds)
        )
    )
    comparison: dict[str, dict[str, float | None]] = {}
    descriptive_compute_metrics = {
        "device",
        "latency_ms_per_sample",
        "latency_ms_per_window",
        "model_inference_latency_ms_per_window",
        "model_inference_throughput_windows_per_second",
        "parameters",
        "real_scalar_parameters",
        "throughput_fps",
        "throughput_windows_per_second",
    }
    for metric in metric_names:
        if metric in descriptive_compute_metrics:
            continue
        fno_values = np.asarray([raw["fno"][seed][metric] for seed in common_seeds], dtype=float)
        unet_values = np.asarray([raw["unet"][seed][metric] for seed in common_seeds], dtype=float)
        if not (np.isfinite(fno_values).all() and np.isfinite(unet_values).all()):
            continue
        differences = fno_values - unet_values  # Positive => FNO has higher error (worse for error metrics).
        ci_low, ci_high = _bootstrap_ci(differences, bootstrap_samples, seed=123)
        comparison[metric] = {
            "mean_fno_minus_unet": float(differences.mean()),
            "ci95_low": ci_low,
            "ci95_high": ci_high,
            "paired_sign_flip_p": _paired_sign_flip_pvalue(differences),
            "n_seeds": float(len(common_seeds)),
        }
    # A benchmark reports several correlated error metrics. Keep the raw exact
    # paired p-value and provide a family-wise-error correction for claims
    # spanning this complete metric family.
    previous = 0.0
    ordered = sorted(comparison.items(), key=lambda item: float(item[1]["paired_sign_flip_p"]))
    total_tests = len(ordered)
    for rank, (_, values) in enumerate(ordered):
        adjusted = min(1.0, max(previous, (total_tests - rank) * float(values["paired_sign_flip_p"])))
        values["holm_bonferroni_p"] = adjusted
        previous = adjusted
    return comparison


def _aggregate(metrics_by_seed: Mapping[int, Mapping[str, float]]) -> dict[str, dict[str, float]]:
    all_keys = sorted(set().union(*(metrics.keys() for metrics in metrics_by_seed.values())))
    result: dict[str, dict[str, float]] = {}
    for key in all_keys:
        values = np.asarray(
            [metrics[key] for metrics in metrics_by_seed.values() if key in metrics and isinstance(metrics[key], (float, int))],
            dtype=float,
        )
        values = values[np.isfinite(values)]
        if not len(values):
            continue
        std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        result[key] = {
            "mean": float(values.mean()),
            "std": std,
            "ci95": float(1.96 * std / math.sqrt(len(values))) if len(values) > 1 else 0.0,
            "n": float(len(values)),
        }
    return result


def run_benchmark(config: BenchmarkConfig) -> dict[str, Any]:
    checkpoints_root = Path(config.checkpoints_dir).expanduser().resolve()
    raw: dict[str, dict[int, dict[str, float]]] = {"fno": {}, "unet": {}}
    for kind in ("fno", "unet"):
        for seed in config.seeds:
            set_seed(seed)
            checkpoint = _safe_load_checkpoint(_checkpoint_path(checkpoints_root, kind, seed))
            if int(checkpoint["seed"]) != seed:
                raise DatasetValidationError(
                    f"Checkpoint {_checkpoint_path(checkpoints_root, kind, seed)} declares seed {checkpoint['seed']}, not {seed}."
                )
            print(f"Evaluating {kind.upper()} seed={seed}")
            raw[kind][seed] = evaluate_checkpoint(checkpoint, config.data_dir, config, kind)
    result = {
        "metadata": asdict(config),
        "raw_seed_metrics": raw,
        "aggregate": {kind: _aggregate(values) for kind, values in raw.items()},
        "paired_fno_minus_unet": paired_comparison(raw, config.bootstrap_samples),
        "metric_definitions": {
            "gwrmse": "Reference-gradient-weighted RMSE; lower is better.",
            "interior_edge_rmse": "Error at the outer interior cells supplied by BubbleML, not a physical wall residual.",
            "interface_*": "Computed around true dfun-derived vapor/liquid interfaces; lower is better.",
            "rollout_*": "True autoregressive error against preprocessed future frames; lower is better.",
        },
    }
    output = Path(config.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "benchmark_results.json").write_text(json.dumps(result, indent=2) + "\n")
    with (output / "benchmark_summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["model", "seed", "metric", "value"])
        for kind, by_seed in raw.items():
            for seed, metrics in by_seed.items():
                for metric, value in sorted(metrics.items()):
                    writer.writerow([kind, seed, metric, value])
    return result


def _parse_seeds(value: str) -> tuple[int, ...]:
    values = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark trained BubbleML FNO and U-Net checkpoints on held-out trajectories.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--checkpoints-dir", default="checkpoints")
    parser.add_argument("--output-dir", default="benchmark_results")
    parser.add_argument("--seeds", type=_parse_seeds, default=DEFAULT_SEEDS)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    parser.add_argument("--fno-device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    parser.add_argument("--use-amp", action="store_true")
    parser.add_argument("--warmup-batches", type=int, default=2)
    parser.add_argument("--rollout-steps", type=int, default=1)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_benchmark(
        BenchmarkConfig(
            data_dir=args.data_dir,
            checkpoints_dir=args.checkpoints_dir,
            output_dir=args.output_dir,
            seeds=args.seeds,
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            device=args.device,
            fno_device=args.fno_device,
            use_amp=args.use_amp,
            warmup_batches=args.warmup_batches,
            rollout_steps=args.rollout_steps,
            bootstrap_samples=args.bootstrap_samples,
        )
    )
    for metric in ("gwrmse", "interior_edge_rmse", "interface_alpha_rmse", "interface_temperature_jump_mae"):
        comparison = result["paired_fno_minus_unet"].get(metric)
        if comparison:
            ci_low, ci_high = comparison["ci95_low"], comparison["ci95_high"]
            ci_text = "95% bootstrap CI unavailable (n=1)" if ci_low is None else f"95% bootstrap CI [{ci_low:.4e}, {ci_high:.4e}]"
            print(
                f"{metric}: FNO-UNet={comparison['mean_fno_minus_unet']:.4e} "
                f"{ci_text} p={comparison['paired_sign_flip_p']:.4g}"
            )


if __name__ == "__main__":
    main()
