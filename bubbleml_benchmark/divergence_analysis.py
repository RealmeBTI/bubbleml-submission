"""Predeclared one-target analysis for divergence-penalized hybrid T-FNO."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from .benchmark import _bootstrap_ci
from .hybrid_analysis import _one_sided_sign_flip_pvalue

MASS_METRIC = "mass_conservation_mae"
MASS_MARGIN = 0.008292845428963615


def analyze(payload: dict[str, Any], bootstrap_samples: int = 10_000) -> dict[str, Any]:
    raw = payload["raw_seed_metrics"]
    if not {"hybrid_div", "unet"}.issubset(raw):
        raise ValueError("Benchmark must contain hybrid_div and unet.")
    hybrid = {int(seed): values for seed, values in raw["hybrid_div"].items()}
    unet = {int(seed): values for seed, values in raw["unet"].items()}
    seeds = sorted(set(hybrid).intersection(unet))
    differences = np.asarray(
        [float(hybrid[seed][MASS_METRIC]) - float(unet[seed][MASS_METRIC]) for seed in seeds],
        dtype=float,
    )
    if len(seeds) != 11:
        raise ValueError(f"Confirmatory analysis requires 11 paired seeds, found {len(seeds)}.")
    if not np.isfinite(differences).all():
        raise ValueError("Mass-conservation differences must be finite.")
    ci_low, ci_high = _bootstrap_ci(differences, bootstrap_samples, seed=123)
    p_value = _one_sided_sign_flip_pvalue(differences - MASS_MARGIN)
    passes = bool(p_value < 0.05 and ci_high is not None and ci_high < MASS_MARGIN)
    return {
        "protocol": {
            "metric": MASS_METRIC,
            "comparator": "unet",
            "margin": MASS_MARGIN,
            "alpha": 0.05,
            "family_size": 1,
            "bootstrap_samples": bootstrap_samples,
        },
        "result": {
            "seeds": seeds,
            "n_seeds": len(seeds),
            "mean_hybrid_div_minus_unet": float(differences.mean()),
            "paired_bootstrap_ci95_low": ci_low,
            "paired_bootstrap_ci95_high": ci_high,
            "noninferiority_sign_flip_p": p_value,
            "holm_noninferiority_p": p_value,
            "noninferior": passes,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    args = parser.parse_args()
    result = analyze(json.loads(Path(args.benchmark_json).read_text()), args.bootstrap_samples)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
