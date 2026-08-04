"""Render temperature and vapor-mask predictions against real BubbleML ground truth."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from .data import (
    CHANNEL_ALPHA,
    CHANNEL_TEMPERATURE,
    ChannelNormalizer,
    TensorSampleDataset,
    channel_index,
)
from .models import ModelSpec, build_model
from .runtime import available_device, fno_device, synchronize


def _load_checkpoint(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return torch.load(path, map_location="cpu", weights_only=True)


@torch.inference_mode()
def render_prediction(
    checkpoint_path: str | Path,
    data_dir: str | Path,
    output_path: str | Path,
    *,
    split: str = "test",
    index: int = 0,
    device_request: str = "auto",
    fno_device_request: str = "auto",
) -> Path:
    checkpoint_path = Path(checkpoint_path).expanduser().resolve()
    checkpoint = _load_checkpoint(checkpoint_path)
    normalizer = ChannelNormalizer.from_state_dict(checkpoint["normalizer"])
    dataset = TensorSampleDataset(data_dir, split=split, normalizer=normalizer)
    if not 0 <= index < len(dataset):
        raise IndexError(f"Sample index {index} is outside {split} split (n={len(dataset)}).")
    spec = ModelSpec.from_state_dict(checkpoint["model_spec"])
    if spec.kind == "fno":
        requested = fno_device_request if fno_device_request != "auto" else device_request
        device = fno_device(requested, spec, dataset[index]["input"].shape[-2:])
    else:
        device = available_device(device_request)
    model = build_model(spec).to(device).eval()
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    sample = dataset[index]
    inputs = sample["input"].unsqueeze(0).to(device)
    prediction = normalizer.decode(model(inputs).float())[0].cpu()
    target = normalizer.decode(sample["target"].unsqueeze(0))[0].cpu()
    synchronize(device)
    temp_index = channel_index(dataset.channel_names, CHANNEL_TEMPERATURE)
    alpha_index = channel_index(dataset.channel_names, CHANNEL_ALPHA)
    fields = (("Temperature", temp_index, "inferno"), ("Vapor mask α", alpha_index, "viridis"))
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    for row, (label, field_index, cmap) in enumerate(fields):
        reference = target[field_index].numpy()
        estimated = prediction[field_index].numpy()
        error = estimated - reference
        if field_index == alpha_index:
            lower, upper = 0.0, 1.0
        else:
            lower, upper = float(min(reference.min(), estimated.min())), float(max(reference.max(), estimated.max()))
        images = (
            axes[row, 0].imshow(reference, cmap=cmap, vmin=lower, vmax=upper, origin="lower"),
            axes[row, 1].imshow(estimated, cmap=cmap, vmin=lower, vmax=upper, origin="lower"),
            axes[row, 2].imshow(error, cmap="coolwarm", origin="lower"),
        )
        for axis, title in zip(
            axes[row, :3],
            (f"Ground truth {label}", f"Prediction {label}", f"Prediction − truth {label}"),
            strict=True,
        ):
            axis.set_title(title)
            axis.set_xticks([])
            axis.set_yticks([])
        fig.colorbar(images[0], ax=axes[row, :2], shrink=0.8)
        fig.colorbar(images[2], ax=axes[row, 2], shrink=0.8)
        phase = target[alpha_index].numpy() > 0.5
        transitions = np.count_nonzero(phase[:, 1:] != phase[:, :-1], axis=1)
        cross_section = int(np.argmax(transitions)) if transitions.any() else reference.shape[0] // 2
        axes[row, 3].plot(reference[cross_section], label="ground truth", linewidth=2)
        axes[row, 3].plot(estimated[cross_section], label="prediction", linewidth=1.5)
        axes[row, 3].set_title(f"{label} cross-section (row {cross_section})")
        axes[row, 3].set_xlabel("x cell")
        axes[row, 3].set_ylabel(label)
        axes[row, 3].legend()
        axes[row, 3].grid(alpha=0.25)
    fig.suptitle(
        f"{checkpoint['model_kind'].upper()} prediction vs. BubbleML ground truth — source frame {sample['timestep']}",
        fontsize=14,
    )
    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot BubbleML temperature and alpha predictions against ground truth.")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--split", default="test", choices=("train", "val", "test"))
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "mps", "cuda"))
    parser.add_argument("--fno-device", default="auto", choices=("auto", "cpu", "mps", "cuda"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    default_output = Path("benchmark_results") / f"field_comparison_{Path(args.checkpoint).stem}_sample{args.index}.png"
    output = render_prediction(
        args.checkpoint,
        args.data_dir,
        args.output or default_output,
        split=args.split,
        index=args.index,
        device_request=args.device,
        fno_device_request=args.fno_device,
    )
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
