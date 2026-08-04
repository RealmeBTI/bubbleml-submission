"""Predeclared Pareto-break analysis for the local-global hybrid T-FNO."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np

from .benchmark import _bootstrap_ci

# Fixed before hybrid training. Each margin is 5% of the relevant 11-seed
# Phase-1 baseline mean in phase1_gpu_decisive_tfno_unet_n11.
PREDECLARED_TESTS = (
    {
        "metric": "mass_conservation_mae",
        "comparator": "unet",
        "margin": 0.008292845428963615,
    },
    {
        "metric": "interface_temperature_rmse",
        "comparator": "tfno",
        "margin": 0.7540349168587817,
    },
    {
        "metric": "interface_temperature_jump_mae",
        "comparator": "tfno",
        "margin": 0.7887777907739986,
    },
)


def _one_sided_sign_flip_pvalue(differences_minus_margin: np.ndarray) -> float:
    """Exact lower-tail paired randomization p-value (H1: mean < 0)."""
    observed = float(differences_minus_margin.mean())
    if len(differences_minus_margin) > 20:
        rng = np.random.default_rng(0)
        signs = rng.choice((-1.0, 1.0), size=(100_000, len(differences_minus_margin)))
        distribution = (signs * differences_minus_margin).mean(axis=1)
        return float((np.count_nonzero(distribution <= observed) + 1) / (len(distribution) + 1))
    else:
        distribution = np.fromiter(
            (
                float((np.asarray(signs) * differences_minus_margin).mean())
                for signs in itertools.product((-1.0, 1.0), repeat=len(differences_minus_margin))
            ),
            dtype=float,
        )
        return float(np.count_nonzero(distribution <= observed) / len(distribution))


def analyze(payload: dict[str, Any], bootstrap_samples: int = 10_000) -> dict[str, Any]:
    raw = payload["raw_seed_metrics"]
    if not {"hybrid_tfno", "tfno", "unet"}.issubset(raw):
        raise ValueError("Benchmark must contain hybrid_tfno, tfno, and unet.")
    outcomes: dict[str, dict[str, Any]] = {}
    for test in PREDECLARED_TESTS:
        metric = str(test["metric"])
        comparator = str(test["comparator"])
        margin = float(test["margin"])
        hybrid_seeds = {int(seed): values for seed, values in raw["hybrid_tfno"].items()}
        baseline_seeds = {int(seed): values for seed, values in raw[comparator].items()}
        seeds = sorted(set(hybrid_seeds).intersection(baseline_seeds))
        differences = np.asarray(
            [float(hybrid_seeds[seed][metric]) - float(baseline_seeds[seed][metric]) for seed in seeds]
        )
        if not np.isfinite(differences).all():
            raise ValueError(f"Non-finite paired differences for {metric}.")
        ci_low, ci_high = _bootstrap_ci(differences, bootstrap_samples, seed=123)
        p_value = _one_sided_sign_flip_pvalue(differences - margin)
        outcomes[metric] = {
            "comparator": comparator,
            "margin": margin,
            "seeds": seeds,
            "n_seeds": len(seeds),
            "mean_hybrid_minus_comparator": float(differences.mean()),
            "paired_bootstrap_ci95_low": ci_low,
            "paired_bootstrap_ci95_high": ci_high,
            "noninferiority_sign_flip_p": p_value,
        }

    previous = 0.0
    ordered = sorted(outcomes.values(), key=lambda row: row["noninferiority_sign_flip_p"])
    for rank, row in enumerate(ordered):
        adjusted = min(
            1.0,
            max(previous, (len(ordered) - rank) * row["noninferiority_sign_flip_p"]),
        )
        row["holm_noninferiority_p"] = adjusted
        row["noninferior"] = bool(
            adjusted < 0.05
            and row["paired_bootstrap_ci95_high"] is not None
            and row["paired_bootstrap_ci95_high"] < row["margin"]
        )
        row["superior"] = bool(
            row["noninferior"]
            and row["mean_hybrid_minus_comparator"] < 0
            and row["paired_bootstrap_ci95_high"] < 0
        )
        previous = adjusted

    return {
        "protocol": {
            "family": "three predeclared lower-is-better Pareto targets",
            "alpha": 0.05,
            "margin_policy": "fixed 5% of the relevant Phase-1 11-seed baseline mean",
            "decision_rule": "Holm p < 0.05 and paired bootstrap upper CI < margin",
            "bootstrap_samples": bootstrap_samples,
        },
        "tests": outcomes,
        "pareto_break": all(row["noninferior"] for row in outcomes.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    args = parser.parse_args()
    source = Path(args.benchmark_json)
    result = analyze(json.loads(source.read_text()), args.bootstrap_samples)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
