"""Refresh paired statistics in an existing paper-benchmark JSON without re-evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import paired_comparison


def refresh(payload: dict[str, Any], bootstrap_samples: int = 10_000) -> dict[str, Any]:
    raw = payload["raw_seed_metrics"]
    numeric = {
        kind: {
            int(seed): {
                name: float(value)
                for name, value in metrics.items()
                if isinstance(value, (int, float))
            }
            for seed, metrics in rows.items()
        }
        for kind, rows in raw.items()
    }

    def versus(comparator: str) -> dict[str, Any]:
        if comparator not in numeric:
            return {}
        return {
            kind: paired_comparison(
                {"fno": rows, "unet": numeric[comparator]}, bootstrap_samples
            )
            for kind, rows in numeric.items()
            if kind != comparator
        }

    payload["pairwise_model_minus_unet"] = versus("unet")
    payload["pairwise_model_minus_tfno"] = versus("tfno")
    payload["pairwise_model_minus_hybrid_tfno"] = versus("hybrid_tfno")
    payload["paired_fno_minus_unet"] = payload["pairwise_model_minus_unet"].get(
        "fno", {}
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-json", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    args = parser.parse_args()
    payload = refresh(json.loads(args.benchmark_json.read_text()), args.bootstrap_samples)
    args.benchmark_json.write_text(json.dumps(payload, indent=2) + "\n")
    print(args.benchmark_json)


if __name__ == "__main__":
    main()
