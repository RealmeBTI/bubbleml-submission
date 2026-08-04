"""Generate the core snapshot and Pareto figures for the manuscript."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import torch

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .data import CHANNEL_ALPHA, CHANNEL_TEMPERATURE, ChannelNormalizer
from .paper_benchmark import _safe_checkpoint
from .paper_models import PaperModelSpec, build_paper_model
from .runtime import available_device
from .temporal import TemporalBundleDataset

DISPLAY_NAMES = {
    "tfno": "T-FNO",
    "unet": "U-Net",
    "hybrid_tfno": "Local-global hybrid",
    "hybrid_div": "Divergence hybrid",
}


def bootstrap_mean_interval(
    values: list[float], samples: int = 10_000, seed: int = 4171
) -> tuple[float, float]:
    if len(values) < 2:
        return (float("nan"), float("nan"))
    array = np.asarray(values, dtype=float)
    generator = np.random.default_rng(seed)
    draws = generator.choice(array, size=(samples, len(array)), replace=True).mean(axis=1)
    low, high = np.quantile(draws, (0.025, 0.975))
    return float(low), float(high)


def paired_model_intervals(
    raw: dict[str, dict[str, dict[str, float]]],
    metric: str,
    kinds: tuple[str, ...],
    *,
    samples: int = 10_000,
    seed: int = 4171,
) -> dict[str, tuple[float, float]]:
    """Bootstrap model means using one shared paired-seed resample."""
    common = sorted(set.intersection(*(set(raw[kind]) for kind in kinds)), key=int)
    if len(common) < 2:
        return {kind: (float("nan"), float("nan")) for kind in kinds}
    values = np.asarray(
        [[float(raw[kind][paired_seed][metric]) for paired_seed in common] for kind in kinds],
        dtype=float,
    )
    generator = np.random.default_rng(seed)
    indices = generator.integers(0, len(common), size=(samples, len(common)))
    draws = values[:, indices].mean(axis=2)
    return {
        kind: tuple(float(value) for value in np.quantile(draws[index], (0.025, 0.975)))
        for index, kind in enumerate(kinds)
    }


def plot_pareto(payload: dict[str, Any], destination: Path) -> None:
    raw = payload["raw_seed_metrics"]
    kinds = ("tfno", "unet", "hybrid_tfno", "hybrid_div")
    interface_intervals = paired_model_intervals(
        raw, "interface_temperature_rmse", kinds, seed=4171
    )
    mass_intervals = paired_model_intervals(raw, "mass_conservation_mae", kinds, seed=5171)
    fig, axis = plt.subplots(figsize=(7.2, 5.4))
    for kind in kinds:
        rows = raw[kind]
        interface = [float(row["interface_temperature_rmse"]) for row in rows.values()]
        mass = [float(row["mass_conservation_mae"]) for row in rows.values()]
        x = float(np.mean(interface))
        y = float(np.mean(mass))
        x_low, x_high = interface_intervals[kind]
        y_low, y_high = mass_intervals[kind]
        axis.errorbar(
            x,
            y,
            xerr=[[x - x_low], [x_high - x]],
            yerr=[[y - y_low], [y_high - y]],
            marker="o",
            markersize=8,
            capsize=4,
            linestyle="none",
            label=DISPLAY_NAMES[kind],
        )
    axis.set(
        xlabel="Interface-temperature RMSE (lower is better)",
        ylabel="Mass-conservation MAE (lower is better)",
        title="Interface fidelity versus conservation",
    )
    axis.grid(alpha=0.2)
    axis.legend(frameon=False)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=220)
    plt.close(fig)


@torch.inference_mode()
def plot_snapshots(
    data_dir: Path,
    checkpoints_dir: Path,
    output_dir: Path,
    *,
    seed: int,
    source_contains: str,
    device_name: str,
) -> None:
    checkpoints = {
        kind: _safe_checkpoint(checkpoints_dir / f"{kind}_seed_{seed}.pt")
        for kind in ("tfno", "unet")
    }
    reference = checkpoints["tfno"]
    normalizer = ChannelNormalizer.from_state_dict(reference["normalizer"])
    dataset = TemporalBundleDataset(
        data_dir,
        "test",
        normalizer,
        history_size=int(reference["history_size"]),
        future_size=int(reference["future_size"]),
        rollout_bundles=3,
        cache_frames=True,
    )
    selected = next(
        (
            index
            for index, window in enumerate(dataset.windows)
            if source_contains
            in Path(str(dataset.base.entries[window[dataset.history_size - 1]]["source"])).stem
        ),
        None,
    )
    if selected is None:
        raise ValueError(f"No test window source contains {source_contains!r}.")
    sample = dataset[selected]
    target_bundles = sample["rollout_targets"]
    target = torch.cat(
        [dataset.decode_frames(bundle, dataset.future_size) for bundle in target_bundles], dim=0
    )
    device = available_device(device_name)
    predictions: dict[str, torch.Tensor] = {}
    for kind, checkpoint in checkpoints.items():
        spec = PaperModelSpec.from_state_dict(checkpoint["model_spec"])
        model = build_paper_model(spec).to(device).eval()
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        current = sample["input"].unsqueeze(0).to(device)
        bundles: list[torch.Tensor] = []
        for _ in range(3):
            current = model(current)
            bundles.append(dataset.decode_frames(current[0].float().cpu(), dataset.future_size))
        predictions[kind] = torch.cat(bundles, dim=0)

    horizons = (dataset.future_size - 1, 2 * dataset.future_size - 1, 3 * dataset.future_size - 1)
    for channel_name, filename, cmap in (
        (CHANNEL_TEMPERATURE, "temperature_snapshots.png", "inferno"),
        (CHANNEL_ALPHA, "alpha_snapshots.png", "viridis"),
    ):
        channel = dataset.channel_names.index(channel_name)
        all_fields = [target[:, channel], predictions["tfno"][:, channel], predictions["unet"][:, channel]]
        vmin = min(float(fields[list(horizons)].min()) for fields in all_fields)
        vmax = max(float(fields[list(horizons)].max()) for fields in all_fields)
        fig, axes = plt.subplots(3, 3, figsize=(9.6, 8.2), constrained_layout=True)
        image = None
        for row, (label, fields) in enumerate(
            (("Ground truth", target[:, channel]), ("T-FNO", predictions["tfno"][:, channel]), ("U-Net", predictions["unet"][:, channel]))
        ):
            for column, horizon in enumerate(horizons):
                image = axes[row, column].imshow(
                    fields[horizon], origin="lower", cmap=cmap, vmin=vmin, vmax=vmax
                )
                if row == 0:
                    axes[row, column].set_title(f"Forecast horizon {horizon + 1}")
                if column == 0:
                    axes[row, column].set_ylabel(label)
                axes[row, column].set_xticks([])
                axes[row, column].set_yticks([])
        if image is not None:
            fig.colorbar(image, ax=axes, shrink=0.82, label=channel_name.replace("_", " "))
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / filename, dpi=220)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--checkpoints-dir", type=Path, required=True)
    parser.add_argument("--benchmark-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--source-contains", default="Twall-110")
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    args = parser.parse_args()
    payload = json.loads(args.benchmark_json.read_text())
    plot_pareto(payload, args.output_dir / "pareto_interface_vs_conservation.png")
    plot_snapshots(
        args.data_dir,
        args.checkpoints_dir,
        args.output_dir,
        seed=args.seed,
        source_contains=args.source_contains,
        device_name=args.device,
    )


if __name__ == "__main__":
    main()
