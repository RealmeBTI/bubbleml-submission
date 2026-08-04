"""Five-field evaluation for temporal FNO/TFNO/FFNO/U-Net checkpoints."""

from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader

from .benchmark import _aggregate, paired_comparison
from .data import ChannelNormalizer, DatasetValidationError
from .metrics import MetricAccumulator, gradient_weighted_rmse, sample_metrics
from .paper_models import PaperModelKind, PaperModelSpec, build_paper_model, real_scalar_parameters
from .paper_train import DEFAULT_PAPER_MODELS, DEFAULT_PAPER_SEEDS, PAPER_MODEL_CHOICES
from .runtime import available_device, set_seed, synchronize
from .temporal import TemporalBundleDataset


@dataclass(frozen=True)
class PaperBenchmarkConfig:
    data_dir: str
    checkpoints_dir: str = "checkpoints/phase1_paper"
    output_dir: str = "benchmark_results/phase1_paper"
    seeds: tuple[int, ...] = DEFAULT_PAPER_SEEDS
    models: tuple[PaperModelKind, ...] = DEFAULT_PAPER_MODELS
    batch_size: int = 8
    num_workers: int = 0
    cache_frames: bool = False
    rollout_bundles: int = 1
    bootstrap_samples: int = 10_000
    device: str = "auto"


def _safe_checkpoint(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required checkpoint: {path}")
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    required = {
        "format",
        "model_kind",
        "seed",
        "git_commit",
        "model_spec",
        "model_state_dict",
        "normalizer",
        "channel_names",
        "history_size",
        "future_size",
    }
    missing = required.difference(checkpoint)
    if missing:
        raise DatasetValidationError(f"{path} is missing checkpoint fields {sorted(missing)}")
    if checkpoint["format"] != "bubbleml-paper-five-field-v1":
        raise DatasetValidationError(f"Unsupported checkpoint format in {path}")
    return checkpoint


def _loader(dataset: TemporalBundleDataset, config: PaperBenchmarkConfig) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        persistent_workers=config.num_workers > 0,
    )


@torch.inference_mode()
def evaluate(
    checkpoint: dict[str, Any],
    config: PaperBenchmarkConfig,
    kind: PaperModelKind,
) -> dict[str, Any]:
    spec = PaperModelSpec.from_state_dict(checkpoint["model_spec"])
    if spec.kind != kind or checkpoint["model_kind"] != kind:
        raise DatasetValidationError(f"Checkpoint kind does not match requested {kind}.")
    normalizer = ChannelNormalizer.from_state_dict(checkpoint["normalizer"])
    dataset = TemporalBundleDataset(
        config.data_dir,
        "test",
        normalizer,
        history_size=int(checkpoint["history_size"]),
        future_size=int(checkpoint["future_size"]),
        rollout_bundles=config.rollout_bundles,
        cache_frames=config.cache_frames,
    )
    if tuple(checkpoint["channel_names"]) != dataset.channel_names:
        raise DatasetValidationError("Checkpoint and test channel schemas differ.")
    model = build_paper_model(spec)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    requested_device = available_device(config.device)
    try:
        model = model.to(requested_device).eval()
        first = dataset[0]["input"].unsqueeze(0).to(requested_device)
        _ = model(first)
        synchronize(requested_device)
        device = requested_device
    except (RuntimeError, NotImplementedError) as exc:
        if requested_device.type != "mps" or kind == "unet":
            raise
        print(f"[WARN] {kind} MPS evaluation failed ({exc}); using CPU.")
        device = torch.device("cpu")
        model = build_paper_model(spec).to(device).eval()
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)

    loader = _loader(dataset, config)
    one_step = MetricAccumulator()
    rollout = MetricAccumulator()
    per_source: dict[str, MetricAccumulator] = {}
    examples = 0
    model_forward_seconds = 0.0
    model_forward_windows = 0
    synchronize(device)
    started = time.perf_counter()
    for batch in loader:
        current = batch["input"].to(device)
        target_bundles = batch["rollout_targets"].to(device)
        for bundle_index in range(config.rollout_bundles):
            synchronize(device)
            forward_started = time.perf_counter()
            prediction = model(current)
            synchronize(device)
            model_forward_seconds += time.perf_counter() - forward_started
            model_forward_windows += int(current.shape[0])
            target = target_bundles[:, bundle_index]
            physical_prediction = dataset.decode_frames(prediction.float(), dataset.future_size)
            physical_target = dataset.decode_frames(target.float(), dataset.future_size)
            for batch_index in range(prediction.shape[0]):
                source_name = Path(str(batch["source"][batch_index])).stem
                source_accumulator = per_source.setdefault(source_name, MetricAccumulator())
                for frame_index in range(dataset.future_size):
                    values = sample_metrics(
                        physical_prediction[batch_index, frame_index],
                        physical_target[batch_index, frame_index],
                        dataset.channel_names,
                        float(batch["dx"][batch_index]),
                        float(batch["dy"][batch_index]),
                    )
                    if bundle_index == 0:
                        one_step.update(values)
                        source_accumulator.update(values)
                    rollout.update({f"rollout_{name}": value for name, value in values.items()})
            alpha_index = dataset.channel_names.index("alpha_vapor_mask")
            alpha_prediction = physical_prediction[:, :, alpha_index].flatten(0, 1).unsqueeze(1)
            alpha_target = physical_target[:, :, alpha_index].flatten(0, 1).unsqueeze(1)
            for value in gradient_weighted_rmse(alpha_prediction, alpha_target):
                rollout.update({"rollout_alpha_gwrmse": float(value)})
            if dataset.history_size != dataset.future_size and bundle_index + 1 < config.rollout_bundles:
                raise DatasetValidationError("Autoregressive bundled rollout requires history_size == future_size.")
            current = prediction
        examples += int(batch["input"].shape[0])
    synchronize(device)
    elapsed = time.perf_counter() - started
    result: dict[str, Any] = one_step.mean()
    result.update(rollout.mean())
    result.update(
        {
            "throughput_windows_per_second": examples / elapsed,
            "latency_ms_per_window": 1000 * elapsed / examples,
            "model_inference_throughput_windows_per_second": (
                model_forward_windows / model_forward_seconds
            ),
            "model_inference_latency_ms_per_window": (
                1000 * model_forward_seconds / model_forward_windows
            ),
            "parameters": float(sum(parameter.numel() for parameter in model.parameters())),
            "real_scalar_parameters": float(real_scalar_parameters(model)),
            "device": str(device),
            "per_test_source_one_step": {
                source: accumulator.mean()
                for source, accumulator in sorted(per_source.items())
            },
        }
    )
    return result


def run(config: PaperBenchmarkConfig) -> dict[str, Any]:
    checkpoint_root = Path(config.checkpoints_dir).resolve()
    raw: dict[str, dict[int, dict[str, float | str]]] = {kind: {} for kind in config.models}
    raw_by_source: dict[str, dict[int, dict[str, dict[str, float]]]] = {
        kind: {} for kind in config.models
    }
    commits: set[str] = set()
    for kind in config.models:
        for seed in config.seeds:
            set_seed(seed)
            checkpoint = _safe_checkpoint(checkpoint_root / f"{kind}_seed_{seed}.pt")
            if int(checkpoint["seed"]) != seed:
                raise DatasetValidationError(f"{kind} checkpoint declares the wrong seed.")
            commits.add(str(checkpoint["git_commit"]))
            print(f"Evaluating {kind.upper()} seed={seed}", flush=True)
            evaluated = evaluate(checkpoint, config, kind)
            raw_by_source[kind][seed] = evaluated.pop("per_test_source_one_step")
            raw[kind][seed] = evaluated

    numeric_raw: dict[str, dict[int, dict[str, float]]] = {
        kind: {
            seed: {name: float(value) for name, value in metrics.items() if isinstance(value, (int, float))}
            for seed, metrics in seeds.items()
        }
        for kind, seeds in raw.items()
    }
    pairwise_vs_unet: dict[str, Any] = {}
    if "unet" in numeric_raw:
        for kind, model_metrics in numeric_raw.items():
            if kind != "unet":
                pairwise_vs_unet[kind] = paired_comparison(
                    {"fno": model_metrics, "unet": numeric_raw["unet"]},
                    config.bootstrap_samples,
                )
    pairwise_vs_tfno: dict[str, Any] = {}
    if "tfno" in numeric_raw:
        for kind, model_metrics in numeric_raw.items():
            if kind != "tfno":
                pairwise_vs_tfno[kind] = paired_comparison(
                    {"fno": model_metrics, "unet": numeric_raw["tfno"]},
                    config.bootstrap_samples,
                )
    pairwise_vs_hybrid: dict[str, Any] = {}
    if "hybrid_tfno" in numeric_raw:
        for kind, model_metrics in numeric_raw.items():
            if kind != "hybrid_tfno":
                pairwise_vs_hybrid[kind] = paired_comparison(
                    {"fno": model_metrics, "unet": numeric_raw["hybrid_tfno"]},
                    config.bootstrap_samples,
                )
    result = {
        "metadata": {**asdict(config), "checkpoint_git_commits": sorted(commits)},
        "raw_seed_metrics": raw,
        "raw_seed_metrics_by_test_source": raw_by_source,
        "aggregate": {kind: _aggregate(values) for kind, values in numeric_raw.items()},
        "pairwise_model_minus_unet": pairwise_vs_unet,
        "pairwise_model_minus_tfno": pairwise_vs_tfno,
        "pairwise_model_minus_hybrid_tfno": pairwise_vs_hybrid,
        "paired_fno_minus_unet": pairwise_vs_unet.get("fno", {}),
        "metric_definitions": {
            "one_step": "Mean over all five frames in the first predicted future bundle.",
            "rollout_*": "Mean over every requested autoregressive five-frame bundle.",
            "interior_edge_*": "Outer released cells, not unavailable physical ghost/wall cells.",
            "interface_*": "True dfun-derived interface band; lower is better.",
        },
    }
    output = Path(config.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "benchmark_results.json").write_text(json.dumps(result, indent=2) + "\n")
    with (output / "benchmark_summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("model", "seed", "metric", "value"))
        for kind, seeds in raw.items():
            for seed, metrics in seeds.items():
                for metric, value in sorted(metrics.items()):
                    writer.writerow((kind, seed, metric, value))
    return result


def _csv_ints(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in value.split(",") if item.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--checkpoints-dir", default="checkpoints/phase1_paper")
    parser.add_argument("--output-dir", default="benchmark_results/phase1_paper")
    parser.add_argument("--seeds", type=_csv_ints, default=DEFAULT_PAPER_SEEDS)
    parser.add_argument(
        "--models", nargs="+", choices=PAPER_MODEL_CHOICES, default=DEFAULT_PAPER_MODELS
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--cache-frames", action="store_true")
    parser.add_argument("--rollout-bundles", type=int, default=1)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run(
        PaperBenchmarkConfig(
            data_dir=args.data_dir,
            checkpoints_dir=args.checkpoints_dir,
            output_dir=args.output_dir,
            seeds=args.seeds,
            models=tuple(args.models),
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            cache_frames=args.cache_frames,
            rollout_bundles=args.rollout_bundles,
            bootstrap_samples=args.bootstrap_samples,
            device=args.device,
        )
    )
    for kind, metrics in result["pairwise_model_minus_unet"].items():
        value = metrics.get("gwrmse")
        if value:
            print(f"{kind}-unet GWRMSE={value['mean_fno_minus_unet']:.6e} p={value['paired_sign_flip_p']:.4g}")


if __name__ == "__main__":
    main()
