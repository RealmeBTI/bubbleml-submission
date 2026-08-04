"""Recompute validation data, divergence, and interface metrics from checkpoints."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader

from .data import ChannelNormalizer
from .paper_benchmark import _safe_checkpoint
from .paper_models import PaperModelKind, PaperModelSpec, build_paper_model
from .paper_train import PAPER_MODEL_CHOICES, _validation_losses
from .runtime import available_device
from .temporal import TemporalBundleDataset


@dataclass(frozen=True)
class ValidationDiagnosticsConfig:
    data_dir: str
    checkpoints_dir: str
    output: str
    models: tuple[PaperModelKind, ...]
    seeds: tuple[int, ...]
    batch_size: int = 8
    cache_frames: bool = False
    device: str = "auto"


def run(config: ValidationDiagnosticsConfig) -> dict[str, Any]:
    result: dict[str, Any] = {"metadata": asdict(config), "models": {}}
    device = available_device(config.device)
    for kind in config.models:
        result["models"][kind] = {}
        for seed in config.seeds:
            checkpoint = _safe_checkpoint(
                Path(config.checkpoints_dir) / f"{kind}_seed_{seed}.pt"
            )
            spec = PaperModelSpec.from_state_dict(checkpoint["model_spec"])
            normalizer = ChannelNormalizer.from_state_dict(checkpoint["normalizer"])
            dataset = TemporalBundleDataset(
                config.data_dir,
                "val",
                normalizer,
                history_size=int(checkpoint["history_size"]),
                future_size=int(checkpoint["future_size"]),
                cache_frames=config.cache_frames,
            )
            model = build_paper_model(spec)
            model.load_state_dict(checkpoint["model_state_dict"], strict=True)
            model = model.to(device).eval()
            loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=False)
            mse, divergence, interface_temperature = _validation_losses(
                model,
                loader,
                device,
                normalizer,
                dataset.channel_names,
                dataset.future_size,
            )
            result["models"][kind][str(seed)] = {
                "validation_mse": mse,
                "validation_spectral_divergence_mae": divergence,
                "validation_interface_temperature_rmse": interface_temperature,
                "device": str(device),
            }
    destination = Path(config.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    return result


def _csv_ints(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--checkpoints-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--models", nargs="+", choices=PAPER_MODEL_CHOICES, required=True)
    parser.add_argument("--seeds", type=_csv_ints, required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--cache-frames", action="store_true")
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    args = parser.parse_args()
    run(
        ValidationDiagnosticsConfig(
            data_dir=args.data_dir,
            checkpoints_dir=args.checkpoints_dir,
            output=args.output,
            models=tuple(args.models),
            seeds=args.seeds,
            batch_size=args.batch_size,
            cache_frames=args.cache_frames,
            device=args.device,
        )
    )


if __name__ == "__main__":
    main()
