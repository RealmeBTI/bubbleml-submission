#!/usr/bin/env python3
"""Export reviewer-readable per-seed primary metrics from stored benchmark JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METRICS = ("gwrmse", "interface_temperature_rmse", "interface_temperature_jump_mae", "mass_conservation_mae")


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    output = ROOT / "submission/supplementary"
    output.mkdir(parents=True, exist_ok=True)
    sources = [
        ("tutorial_canonical_cuda_48x48", load("benchmark_results/resolution_control_48x48/benchmark_results.json"), ("tfno", "unet")),
        ("tutorial_zero_penalty_hybrid", load("benchmark_results/tier1_hybrid_n11/benchmark_results.json"), ("hybrid_tfno",)),
        ("tutorial_divergence_hybrid_030", load("benchmark_results/lambda_sensitivity_030_n11/benchmark_results.json"), ("hybrid_div",)),
    ]
    destination = output / "per_seed_primary_metrics.csv"
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("experiment", "model", "seed", *METRICS))
        for experiment, payload, models in sources:
            for model in models:
                rows = payload["raw_seed_metrics"][model]
                for seed in sorted(rows, key=int):
                    writer.writerow((experiment, model, int(seed), *(f"{float(rows[seed][metric]):.12g}" for metric in METRICS)))

    lambda_payload = load("benchmark_results/lambda_sensitivity/lambda_sensitivity_results.json")
    lambda_destination = output / "lambda_sensitivity_summary.csv"
    with lambda_destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("lambda_div", "eligible", "validation_mse", "validation_spectral_divergence_mae", "validation_interface_temperature_rmse"))
        for value, row in lambda_payload["candidates"].items():
            writer.writerow((value, row["eligible"], *(f"{float(row['metrics'][metric]['mean']):.12g}" for metric in ("validation_mse", "validation_spectral_divergence_mae", "validation_interface_temperature_rmse"))))
    print(destination)
    print(lambda_destination)


if __name__ == "__main__":
    main()
