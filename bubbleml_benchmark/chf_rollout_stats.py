"""Aggregate paired multi-seed Phase 4 dry-area rollout results."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .benchmark import _aggregate, paired_comparison


@dataclass(frozen=True)
class CHFRolloutStatisticsConfig:
    results_dir: str
    output_path: str
    seeds: tuple[int, ...]
    bootstrap_samples: int = 10_000
    horizon: int = 164


def _dry_area_mae(result: dict[str, Any], kind: str) -> float:
    prediction = result["signals"][kind]
    target = result["signals"]["ground_truth"]
    if len(prediction) != len(target) or not prediction:
        raise ValueError(f"{kind} dry-area signal is empty or has a mismatched length.")
    return sum(abs(float(value) - float(truth)) for value, truth in zip(prediction, target)) / len(target)


def _seed_metrics(result: dict[str, Any], kind: str, horizon: int) -> dict[str, float]:
    summaries = result["horizon_metrics"][kind]
    endpoint = summaries.get(str(horizon))
    if endpoint is None:
        raise ValueError(f"{kind} result does not contain the required horizon {horizon}.")
    values = {
        "cumulative_dry_area_mae": _dry_area_mae(result, kind),
        "false_alarm_frame_count": float(result["events"][kind]["frames_at_or_above_threshold"]),
    }
    for name, value in endpoint.items():
        if isinstance(value, (int, float)):
            values[f"horizon_{horizon}_{name}"] = float(value)
    return values


def run(config: CHFRolloutStatisticsConfig) -> dict[str, Any]:
    root = Path(config.results_dir).expanduser().resolve()
    raw: dict[str, dict[int, dict[str, float]]] = {"tfno": {}, "unet": {}}
    provenance: dict[str, dict[int, dict[str, Any]]] = {"tfno": {}, "unet": {}}
    for seed in config.seeds:
        source = root / f"seed_{seed}" / "rollout_results.json"
        if not source.is_file():
            raise FileNotFoundError(f"Missing required rollout result: {source}")
        result = json.loads(source.read_text())
        if int(result["source"]["autoregressive_steps"]) != config.horizon:
            raise ValueError(f"{source} is not a {config.horizon}-step rollout.")
        for kind, metrics_by_seed in raw.items():
            if int(result["provenance"][kind]["checkpoint_seed"]) != seed:
                raise ValueError(f"{source} has a {kind} checkpoint with the wrong seed.")
            metrics_by_seed[seed] = _seed_metrics(result, kind, config.horizon)
            provenance[kind][seed] = result["provenance"][kind]

    # ``paired_comparison`` is the established unchanged bootstrap, exact
    # sign-flip, and Holm--Bonferroni implementation. Its historical "fno"
    # key is simply populated with T-FNO metrics here.
    paired = paired_comparison(
        {"fno": raw["tfno"], "unet": raw["unet"]}, config.bootstrap_samples
    )
    result = {
        "metadata": {
            **asdict(config),
            "comparison": "tfno_minus_unet",
            "statistics": "Existing paired bootstrap, exact sign-flip, and Holm-Bonferroni code.",
        },
        "raw_seed_metrics": raw,
        "aggregate": {kind: _aggregate(values) for kind, values in raw.items()},
        "paired_tfno_minus_unet": paired,
        "provenance": provenance,
    }
    output = Path(config.output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def _csv_ints(value: str) -> tuple[int, ...]:
    result = tuple(int(item) for item in value.split(",") if item.strip())
    if not result:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--seeds", type=_csv_ints, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--horizon", type=int, default=164)
    args = parser.parse_args()
    output = run(
        CHFRolloutStatisticsConfig(
            results_dir=args.results_dir,
            output_path=args.output_path,
            seeds=args.seeds,
            bootstrap_samples=args.bootstrap_samples,
            horizon=args.horizon,
        )
    )
    for metric in ("cumulative_dry_area_mae", "false_alarm_frame_count"):
        values = output["paired_tfno_minus_unet"][metric]
        print(
            f"{metric}: tfno-unet={values['mean_fno_minus_unet']:.6g}; "
            f"Holm p={values['holm_bonferroni_p']:.6g}"
        )


if __name__ == "__main__":
    main()
