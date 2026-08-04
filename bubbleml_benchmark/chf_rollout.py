"""Full autoregressive T-FNO/U-Net rollout for a dry-area CHF proxy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

import matplotlib
import torch

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .data import CHANNEL_ALPHA, ChannelNormalizer, DatasetValidationError, TensorSampleDataset
from .metrics import sample_metrics
from .paper_benchmark import _safe_checkpoint
from .paper_models import PaperModelKind, PaperModelSpec, build_paper_model
from .runtime import available_device, synchronize


@dataclass(frozen=True)
class CHFRolloutConfig:
    data_dir: str
    tfno_checkpoint: str
    unet_checkpoint: str
    output_dir: str = "benchmark_results/phase4_chf_rollout"
    heater_rows: int = 4
    alpha_threshold: float = 0.5
    baseline_frames: int = 20
    event_rise: float = 0.10
    event_minimum: float = 0.10
    sustain_frames: int = 3
    horizons: tuple[int, ...] = (5, 10, 20, 40, 80, 160)
    device: str = "auto"


def dry_area_fraction(
    frames: torch.Tensor,
    alpha_index: int,
    heater_rows: int,
    alpha_threshold: float,
) -> torch.Tensor:
    """Return vapor-covered fraction in cells immediately above the heater."""
    if frames.ndim != 4:
        raise ValueError("frames must have shape TxCxHxW")
    if not 1 <= heater_rows <= frames.shape[-2]:
        raise ValueError("heater_rows must be within the spatial height")
    if not 0.0 <= alpha_threshold <= 1.0:
        raise ValueError("alpha_threshold must lie in [0, 1]")
    heater_alpha = frames[:, alpha_index, :heater_rows, :]
    return (heater_alpha > alpha_threshold).float().mean(dim=(-2, -1))


def protocol_event_threshold(
    ground_truth_signal: torch.Tensor,
    baseline_frames: int,
    event_rise: float,
    event_minimum: float,
) -> tuple[float, float]:
    """Build a documented baseline-relative dry-area threshold."""
    if ground_truth_signal.ndim != 1 or ground_truth_signal.numel() == 0:
        raise ValueError("ground_truth_signal must be a non-empty vector")
    if baseline_frames < 1 or event_rise < 0 or not 0 <= event_minimum <= 1:
        raise ValueError("Invalid CHF event threshold settings")
    count = min(baseline_frames, ground_truth_signal.numel())
    baseline = float(ground_truth_signal[:count].median().item())
    threshold = max(event_minimum, baseline + event_rise)
    return baseline, threshold


def first_sustained_crossing(
    signal: torch.Tensor, threshold: float, sustain_frames: int
) -> int | None:
    """Return the zero-based start of the first sustained threshold crossing."""
    if signal.ndim != 1 or sustain_frames < 1:
        raise ValueError("signal must be one-dimensional and sustain_frames positive")
    above = signal >= threshold
    for index in range(max(0, signal.numel() - sustain_frames + 1)):
        if bool(above[index : index + sustain_frames].all()):
            return index
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str:
    completed = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_test_trajectory(
    data_dir: str,
) -> tuple[TensorSampleDataset, torch.Tensor, list[int], float, float, str]:
    dataset = TensorSampleDataset(data_dir, split="test")
    sources = {str(entry["source"]) for entry in dataset.entries}
    if len(sources) != 1:
        raise DatasetValidationError(
            f"Phase 4 requires exactly one held-out trajectory; found {len(sources)}."
        )
    ordered = sorted(range(len(dataset)), key=lambda index: int(dataset.entries[index]["timestep"]))
    timesteps = [int(dataset.entries[index]["timestep"]) for index in ordered]
    if any(right - left != 1 for left, right in pairwise(timesteps)):
        raise DatasetValidationError("Held-out trajectory timesteps are not contiguous.")
    items = [dataset.raw_item(index) for index in ordered]
    frames = torch.stack([item["input"].float() for item in items])
    return (
        dataset,
        frames,
        timesteps,
        float(items[0]["dx"]),
        float(items[0]["dy"]),
        sources.pop(),
    )


def _wall_temperature(source: str) -> float | None:
    match = re.search(r"Twall[-_]?([0-9]+(?:\.[0-9]+)?)", Path(source).stem, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _prepare_model(
    checkpoint_path: Path,
    expected_kind: PaperModelKind,
    channel_names: tuple[str, ...],
    requested_device: torch.device,
) -> tuple[torch.nn.Module, ChannelNormalizer, torch.device, dict[str, Any]]:
    checkpoint = _safe_checkpoint(checkpoint_path)
    if checkpoint["model_kind"] != expected_kind:
        raise DatasetValidationError(f"{checkpoint_path} is not a {expected_kind} checkpoint.")
    if tuple(checkpoint["channel_names"]) != channel_names:
        raise DatasetValidationError("Checkpoint and test trajectory channel schemas differ.")
    if int(checkpoint["history_size"]) != int(checkpoint["future_size"]):
        raise DatasetValidationError(
            "Full bundled autoregression requires equal history and future sizes."
        )
    spec = PaperModelSpec.from_state_dict(checkpoint["model_spec"])
    model = build_paper_model(spec)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    try:
        model = model.to(requested_device).eval()
        device = requested_device
    except (RuntimeError, NotImplementedError):
        if requested_device.type != "mps" or expected_kind == "unet":
            raise
        device = torch.device("cpu")
        model = build_paper_model(spec).to(device).eval()
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    return model, ChannelNormalizer.from_state_dict(checkpoint["normalizer"]), device, checkpoint


@torch.inference_mode()
def _autoregressive_rollout(
    model: torch.nn.Module,
    normalizer: ChannelNormalizer,
    device: torch.device,
    physical_history: torch.Tensor,
    steps: int,
    future_size: int,
) -> torch.Tensor:
    encoded_history = normalizer.encode(physical_history).flatten(0, 1).unsqueeze(0).to(device)
    current = encoded_history
    predictions: list[torch.Tensor] = []
    blocks = math.ceil(steps / future_size)
    for _ in range(blocks):
        encoded_prediction = model(current)
        shaped = encoded_prediction.view(
            1,
            future_size,
            normalizer.channels,
            *encoded_prediction.shape[-2:],
        )
        physical = normalizer.decode(shaped.flatten(0, 1).float()).view_as(shaped)
        predictions.append(physical[0].cpu())
        current = encoded_prediction
    synchronize(device)
    return torch.cat(predictions)[:steps]


def _event_result(
    ground_truth_crossing: int | None,
    prediction_crossing: int | None,
    future_timesteps: list[int],
    signal: torch.Tensor,
    threshold: float,
    sustain_frames: int,
) -> dict[str, Any]:
    runs: list[int] = []
    current_run = 0
    for is_above in signal >= threshold:
        if bool(is_above):
            current_run += 1
        elif current_run:
            runs.append(current_run)
            current_run = 0
    if current_run:
        runs.append(current_run)
    result: dict[str, Any] = {
        "ground_truth_rollout_step": None
        if ground_truth_crossing is None
        else ground_truth_crossing + 1,
        "prediction_rollout_step": None if prediction_crossing is None else prediction_crossing + 1,
        "ground_truth_source_timestep": (
            None if ground_truth_crossing is None else future_timesteps[ground_truth_crossing]
        ),
        "prediction_source_timestep": (
            None if prediction_crossing is None else future_timesteps[prediction_crossing]
        ),
        "lead_steps": None,
        "false_positive": ground_truth_crossing is None and prediction_crossing is not None,
        "false_negative": ground_truth_crossing is not None and prediction_crossing is None,
        "frames_at_or_above_threshold": int((signal >= threshold).sum()),
        "longest_threshold_run": max(runs, default=0),
        "sustained_episode_count": sum(length >= sustain_frames for length in runs),
    }
    if ground_truth_crossing is not None and prediction_crossing is not None:
        result["lead_steps"] = ground_truth_crossing - prediction_crossing
    return result


def _evaluate_prediction(
    prediction: torch.Tensor,
    target: torch.Tensor,
    signal_prediction: torch.Tensor,
    signal_target: torch.Tensor,
    channel_names: tuple[str, ...],
    dx: float,
    dy: float,
    horizons: tuple[int, ...],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    per_frame = [
        sample_metrics(prediction[index], target[index], channel_names, dx, dy)
        for index in range(target.shape[0])
    ]
    summaries: dict[str, dict[str, float]] = {}
    for horizon in sorted(set(horizons)):
        if horizon < 1 or horizon > target.shape[0]:
            continue
        exact = per_frame[horizon - 1]
        through = per_frame[:horizon]
        summary = {
            "dry_fraction_prediction": float(signal_prediction[horizon - 1]),
            "dry_fraction_ground_truth": float(signal_target[horizon - 1]),
            "dry_fraction_absolute_error": float(
                (signal_prediction[horizon - 1] - signal_target[horizon - 1]).abs()
            ),
            "dry_fraction_mae_through_horizon": float(
                (signal_prediction[:horizon] - signal_target[:horizon]).abs().mean()
            ),
            "dry_fraction_rmse_through_horizon": float(
                torch.sqrt((signal_prediction[:horizon] - signal_target[:horizon]).square().mean())
            ),
        }
        summary.update({name: float(value) for name, value in exact.items() if value is not None})
        for name in ("rmse", "gwrmse", "mass_conservation_mae"):
            values = [float(frame[name]) for frame in through if frame[name] is not None]
            summary[f"mean_{name}_through_horizon"] = sum(values) / len(values)
        summaries[str(horizon)] = summary
    return per_frame, summaries


def _plot_signal(
    output: Path,
    all_timesteps: list[int],
    history_signal: torch.Tensor,
    future_timesteps: list[int],
    ground_truth: torch.Tensor,
    model_signals: dict[str, torch.Tensor],
    threshold: float,
    event_results: dict[str, dict[str, Any]],
) -> None:
    fig, axis = plt.subplots(figsize=(12, 6))
    full_ground_truth = torch.cat((history_signal, ground_truth))
    axis.plot(all_timesteps, full_ground_truth, color="black", linewidth=2.2, label="Ground truth")
    colors = {"tfno": "#d95f02", "unet": "#1b9e77"}
    labels = {"tfno": "T-FNO autoregressive", "unet": "U-Net autoregressive"}
    for kind, signal in model_signals.items():
        axis.plot(future_timesteps, signal, color=colors[kind], linewidth=1.8, label=labels[kind])
    axis.axhline(
        threshold, color="#7570b3", linestyle="--", linewidth=1.5, label="Protocol event threshold"
    )
    axis.axvline(
        future_timesteps[0], color="0.5", linestyle=":", label="Autoregressive forecast begins"
    )
    for kind, result in event_results.items():
        crossing = result["prediction_source_timestep"]
        if crossing is not None:
            axis.axvline(crossing, color=colors[kind], linestyle="--", alpha=0.7)
    truth_crossing = event_results["ground_truth"]["ground_truth_source_timestep"]
    if truth_crossing is not None:
        axis.axvline(truth_crossing, color="black", linestyle="--", alpha=0.7)
    axis.set_xlabel("Source trajectory timestep")
    axis.set_ylabel("Dry-area fraction in first four rows above heater")
    axis.set_ylim(-0.02, 1.02)
    axis.set_title(
        "PB Subcooled Twall-100: protocol-defined dry-area signal\n(full autoregressive rollout)"
    )
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def run(config: CHFRolloutConfig) -> dict[str, Any]:
    if config.heater_rows < 1 or config.sustain_frames < 1:
        raise ValueError("heater_rows and sustain_frames must be positive")
    dataset, frames, timesteps, dx, dy, source = _load_test_trajectory(config.data_dir)
    alpha_index = dataset.channel_names.index(CHANNEL_ALPHA)
    history_size = 5
    if frames.shape[0] <= history_size:
        raise DatasetValidationError(
            "Test trajectory is too short for a five-frame rollout history."
        )
    history = frames[:history_size]
    target = frames[history_size:]
    future_timesteps = timesteps[history_size:]
    ground_truth_signal = dry_area_fraction(
        target, alpha_index, config.heater_rows, config.alpha_threshold
    )
    history_signal = dry_area_fraction(
        history, alpha_index, config.heater_rows, config.alpha_threshold
    )
    baseline, event_threshold = protocol_event_threshold(
        ground_truth_signal,
        config.baseline_frames,
        config.event_rise,
        config.event_minimum,
    )
    ground_truth_crossing = first_sustained_crossing(
        ground_truth_signal, event_threshold, config.sustain_frames
    )

    requested_device = available_device(config.device)
    checkpoint_paths = {
        "tfno": Path(config.tfno_checkpoint).expanduser().resolve(),
        "unet": Path(config.unet_checkpoint).expanduser().resolve(),
    }
    predictions: dict[str, torch.Tensor] = {}
    signals: dict[str, torch.Tensor] = {}
    per_frame_metrics: dict[str, list[dict[str, Any]]] = {}
    horizon_metrics: dict[str, dict[str, dict[str, float]]] = {}
    events: dict[str, dict[str, Any]] = {
        "ground_truth": _event_result(
            ground_truth_crossing,
            ground_truth_crossing,
            future_timesteps,
            ground_truth_signal,
            event_threshold,
            config.sustain_frames,
        )
    }
    provenance: dict[str, dict[str, Any]] = {}
    for kind in ("tfno", "unet"):
        model, normalizer, device, checkpoint = _prepare_model(
            checkpoint_paths[kind], kind, dataset.channel_names, requested_device
        )
        future_size = int(checkpoint["future_size"])
        if int(checkpoint["history_size"]) != history_size:
            raise DatasetValidationError("Phase 4 expects the trained five-frame history protocol.")
        prediction = _autoregressive_rollout(
            model, normalizer, device, history, target.shape[0], future_size
        )
        if not bool(torch.isfinite(prediction).all()):
            raise RuntimeError(f"{kind} rollout produced NaN or Inf values.")
        signal = dry_area_fraction(
            prediction, alpha_index, config.heater_rows, config.alpha_threshold
        )
        crossing = first_sustained_crossing(signal, event_threshold, config.sustain_frames)
        per_frame, summaries = _evaluate_prediction(
            prediction,
            target,
            signal,
            ground_truth_signal,
            dataset.channel_names,
            dx,
            dy,
            config.horizons,
        )
        predictions[kind] = prediction
        signals[kind] = signal
        per_frame_metrics[kind] = per_frame
        horizon_metrics[kind] = summaries
        events[kind] = _event_result(
            ground_truth_crossing,
            crossing,
            future_timesteps,
            signal,
            event_threshold,
            config.sustain_frames,
        )
        provenance[kind] = {
            "checkpoint": str(checkpoint_paths[kind]),
            "checkpoint_sha256": _sha256(checkpoint_paths[kind]),
            "checkpoint_seed": int(checkpoint["seed"]),
            "checkpoint_git_commit": str(checkpoint["git_commit"]),
            "best_validation_mse": float(checkpoint["best_validation_mse"]),
            "best_epoch": int(checkpoint["best_epoch"]),
            "device": str(device),
            "alpha_prediction_min": float(prediction[:, alpha_index].min()),
            "alpha_prediction_max": float(prediction[:, alpha_index].max()),
            "all_values_finite": True,
        }

    source_path = Path(source)
    result = {
        "protocol": "phase4-full-autoregressive-five-field-dry-area-v1",
        "evaluation_git_commit": _git_commit(),
        "config": asdict(config),
        "source": {
            "path": source,
            "sha256": _sha256(source_path),
            "wall_temperature_c_from_filename": _wall_temperature(source),
            "heat_flux_series_available": False,
            "first_timestep": timesteps[0],
            "last_timestep": timesteps[-1],
            "history_timesteps": timesteps[:history_size],
            "rollout_timesteps": future_timesteps,
            "trajectory_frames": len(timesteps),
            "autoregressive_steps": len(future_timesteps),
            "dx": dx,
            "dy": dy,
        },
        "event_definition": {
            "region": f"rows 0:{config.heater_rows} (released cells immediately above heater)",
            "alpha_cell_threshold": config.alpha_threshold,
            "baseline_frames": config.baseline_frames,
            "baseline_dry_fraction": baseline,
            "rise_above_baseline": config.event_rise,
            "absolute_minimum": config.event_minimum,
            "event_dry_fraction_threshold": event_threshold,
            "sustain_frames": config.sustain_frames,
            "scope": "illustrative protocol-defined precursor; not a calibrated physical CHF label",
        },
        "provenance": provenance,
        "events": events,
        "signals": {
            "timesteps": future_timesteps,
            "ground_truth": ground_truth_signal.tolist(),
            "tfno": signals["tfno"].tolist(),
            "unet": signals["unet"].tolist(),
        },
        "horizon_metrics": horizon_metrics,
        "per_frame_metrics": per_frame_metrics,
        "notes": [
            "Each five-frame prediction bundle is fed back verbatim as the next input bundle.",
            "No future ground-truth channel is injected and predicted alpha is not clipped before feedback.",
            "The source file stores fixed wall temperature but no wall-heat-flux time series.",
        ],
    }
    output = Path(config.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "rollout_results.json").write_text(json.dumps(result, indent=2) + "\n")
    with (output / "horizon_metrics.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("model", "horizon", "metric", "value"))
        for kind, summaries in horizon_metrics.items():
            for horizon, metrics in summaries.items():
                for name, value in sorted(metrics.items()):
                    writer.writerow((kind, horizon, name, value))
    _plot_signal(
        output / "dry_area_fraction_rollout.png",
        timesteps,
        history_signal,
        future_timesteps,
        ground_truth_signal,
        signals,
        event_threshold,
        events,
    )
    return result


def _csv_ints(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in value.split(",") if item.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--tfno-checkpoint", required=True)
    parser.add_argument("--unet-checkpoint", required=True)
    parser.add_argument("--output-dir", default="benchmark_results/phase4_chf_rollout")
    parser.add_argument("--heater-rows", type=int, default=4)
    parser.add_argument("--alpha-threshold", type=float, default=0.5)
    parser.add_argument("--baseline-frames", type=int, default=20)
    parser.add_argument("--event-rise", type=float, default=0.10)
    parser.add_argument("--event-minimum", type=float, default=0.10)
    parser.add_argument("--sustain-frames", type=int, default=3)
    parser.add_argument("--horizons", type=_csv_ints, default=(5, 10, 20, 40, 80, 160))
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run(
        CHFRolloutConfig(
            data_dir=args.data_dir,
            tfno_checkpoint=args.tfno_checkpoint,
            unet_checkpoint=args.unet_checkpoint,
            output_dir=args.output_dir,
            heater_rows=args.heater_rows,
            alpha_threshold=args.alpha_threshold,
            baseline_frames=args.baseline_frames,
            event_rise=args.event_rise,
            event_minimum=args.event_minimum,
            sustain_frames=args.sustain_frames,
            horizons=args.horizons,
            device=args.device,
        )
    )
    print(json.dumps({"events": result["events"], "provenance": result["provenance"]}, indent=2))


if __name__ == "__main__":
    main()
