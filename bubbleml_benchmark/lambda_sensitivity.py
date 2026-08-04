"""Predeclared three-seed divergence-penalty sensitivity analysis and plot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS = (
    "validation_mse",
    "validation_spectral_divergence_mae",
    "validation_interface_temperature_rmse",
)


def _bootstrap_mean_interval(values: list[float], samples: int, seed: int) -> tuple[float, float]:
    generator = np.random.default_rng(seed)
    array = np.asarray(values, dtype=float)
    draws = generator.choice(array, size=(samples, len(array)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def _rows(payload: dict[str, Any], model: str) -> dict[int, dict[str, float]]:
    return {
        int(seed): {metric: float(row[metric]) for metric in METRICS}
        for seed, row in payload["models"][model].items()
    }


def analyze(
    reference: dict[str, Any],
    candidates: dict[float, dict[str, Any]],
    *,
    bootstrap_samples: int = 10_000,
) -> dict[str, Any]:
    reference_rows = _rows(reference, "hybrid_tfno")
    if len(reference_rows) < 3:
        raise ValueError("Lambda sensitivity requires at least three paired reference seeds.")
    seeds = sorted(reference_rows)
    reference_means = {
        metric: float(np.mean([reference_rows[seed][metric] for seed in seeds]))
        for metric in METRICS
    }
    result_rows: dict[str, Any] = {}
    for index, (lambda_div, payload) in enumerate(sorted(candidates.items())):
        rows = _rows(payload, "hybrid_div")
        if sorted(rows) != seeds:
            raise ValueError(f"lambda_div={lambda_div} does not use the paired reference seeds.")
        metrics: dict[str, Any] = {}
        for metric in METRICS:
            values = [rows[seed][metric] for seed in seeds]
            low, high = _bootstrap_mean_interval(values, bootstrap_samples, 9917 + index)
            metrics[metric] = {
                "mean": float(np.mean(values)),
                "bootstrap_ci95_low": low,
                "bootstrap_ci95_high": high,
            }
        eligible = (
            metrics["validation_mse"]["mean"]
            <= 1.05 * reference_means["validation_mse"]
            and metrics["validation_interface_temperature_rmse"]["mean"]
            <= 1.05 * reference_means["validation_interface_temperature_rmse"]
        )
        result_rows[f"{lambda_div:.10g}"] = {"eligible": eligible, "metrics": metrics}
    eligible_lambdas = [
        value for value, row in result_rows.items() if row["eligible"]
    ]
    if not eligible_lambdas:
        raise ValueError("No lambda candidate satisfies both 5% validation guards.")
    selected = min(
        eligible_lambdas,
        key=lambda value: (
            result_rows[value]["metrics"]["validation_spectral_divergence_mae"]["mean"],
            float(value),
        ),
    )
    return {
        "protocol": {
            "required_seeds": seeds,
            "bootstrap_samples": bootstrap_samples,
            "mse_guard": "candidate mean <= 1.05 * zero-penalty hybrid mean",
            "interface_guard": "candidate mean <= 1.05 * zero-penalty hybrid mean",
            "selection": "lowest mean validation spectral divergence among eligible candidates",
        },
        "reference_means": reference_means,
        "candidates": result_rows,
        "selected_lambda_div": float(selected),
        "selected_is_interior": float(selected) not in (
            min(float(value) for value in result_rows),
            max(float(value) for value in result_rows),
        ),
    }


def plot(result: dict[str, Any], destination: Path) -> None:
    lambdas = np.asarray([float(value) for value in result["candidates"]])
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    labels = (
        ("validation_mse", "Validation MSE"),
        ("validation_spectral_divergence_mae", "Spectral divergence MAE"),
        ("validation_interface_temperature_rmse", "Interface-temperature RMSE"),
    )
    for axis, (metric, label) in zip(axes, labels, strict=True):
        means = np.asarray(
            [result["candidates"][f"{value:.10g}"]["metrics"][metric]["mean"] for value in lambdas]
        )
        lows = np.asarray(
            [result["candidates"][f"{value:.10g}"]["metrics"][metric]["bootstrap_ci95_low"] for value in lambdas]
        )
        highs = np.asarray(
            [result["candidates"][f"{value:.10g}"]["metrics"][metric]["bootstrap_ci95_high"] for value in lambdas]
        )
        axis.errorbar(lambdas, means, yerr=(means - lows, highs - means), marker="o", capsize=3)
        axis.axvline(result["selected_lambda_div"], color="tab:red", linestyle="--", alpha=0.7)
        axis.set(xlabel=r"$\lambda_{div}$", ylabel=label)
        axis.grid(alpha=0.2)
    fig.suptitle("Three-seed divergence-penalty sensitivity (95% seed-bootstrap intervals)")
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=200)
    plt.close(fig)


def _candidate(value: str) -> tuple[float, Path]:
    lambda_text, path = value.split("=", 1)
    return float(lambda_text), Path(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plot", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    args = parser.parse_args()
    candidates = dict(_candidate(value) for value in args.candidate)
    result = analyze(
        json.loads(args.reference.read_text()),
        {value: json.loads(path.read_text()) for value, path in candidates.items()},
        bootstrap_samples=args.bootstrap_samples,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    plot(result, args.plot)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
