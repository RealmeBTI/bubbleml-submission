"""Combine logged Phase 1 histories into a multi-panel loss figure."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_histories(
    experiment_dir: Path,
    output: Path,
    models: tuple[str, ...],
    seeds: tuple[int, ...],
) -> None:
    columns = min(2, len(models))
    rows = math.ceil(len(models) / columns)
    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=(5.5 * columns, 4 * rows),
        sharex=True,
        sharey=True,
        squeeze=False,
    )
    colors = plt.get_cmap("tab10").colors
    for axis, model in zip(axes.flat, models, strict=False):
        for index, seed in enumerate(seeds):
            color = colors[index % len(colors)]
            path = experiment_dir / f"{model}_seed_{seed}" / "results.json"
            result = json.loads(path.read_text())
            history = result["history"]
            epochs = [row["epoch"] for row in history]
            axis.semilogy(
                epochs,
                [row["train_mse"] for row in history],
                color=color,
                linestyle=":",
                alpha=0.75,
            )
            axis.semilogy(
                epochs,
                [row["val_mse"] for row in history],
                color=color,
                label=f"seed {seed}",
            )
        axis.set_title(model.upper().replace("TFNO", "T-FNO").replace("FFNO", "F-FNO"))
        axis.grid(alpha=0.2)
        axis.legend(fontsize=8)
    for axis in axes.flat[len(models) :]:
        axis.set_visible(False)
    fig.supxlabel("Epoch")
    fig.supylabel("Normalized MSE (dotted train, solid validation)")
    fig.suptitle("BubbleML five-field temporal-bundle convergence screening")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, default=Path("experiments/phase1_paper"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/phase1_paper/loss_curves_all.png"),
    )
    parser.add_argument(
        "--models",
        default="fno,tfno,ffno,unet",
        help="Comma-separated model names.",
    )
    parser.add_argument(
        "--seeds",
        default="42,100,1234",
        help="Comma-separated integer seeds.",
    )
    args = parser.parse_args()
    models = tuple(value.strip().lower() for value in args.models.split(",") if value.strip())
    seeds = tuple(int(value) for value in args.seeds.split(",") if value.strip())
    if not models or not seeds:
        parser.error("--models and --seeds must each contain at least one value")
    plot_histories(args.experiment_dir, args.output, models, seeds)


if __name__ == "__main__":
    main()
