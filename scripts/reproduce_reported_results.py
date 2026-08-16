#!/usr/bin/env python3
"""Reviewer-facing, dependency-free audit of the manuscript's key stored results."""

from __future__ import annotations

import argparse
import html
import itertools
import json
import math
from pathlib import Path
from statistics import fmean


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def assert_close(label: str, actual: float, expected: float, tolerance: float = 5e-8) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance):
        raise AssertionError(f"{label}: got {actual:.12g}, expected {expected:.12g}")


def exact_two_sided_sign_flip(differences: list[float]) -> float:
    observed = abs(fmean(differences))
    distribution = (
        abs(fmean(sign * value for sign, value in zip(signs, differences, strict=True)))
        for signs in itertools.product((-1.0, 1.0), repeat=len(differences))
    )
    count = sum(value >= observed - 1e-15 for value in distribution)
    return count / (2 ** len(differences))


def exact_lower_sign_flip(values: list[float]) -> float:
    observed = fmean(values)
    distribution = (
        fmean(sign * value for sign, value in zip(signs, values, strict=True))
        for signs in itertools.product((-1.0, 1.0), repeat=len(values))
    )
    count = sum(value <= observed + 1e-15 for value in distribution)
    return count / (2 ** len(values))


def paired_values(payload: dict, model_a: str, model_b: str, metric: str) -> tuple[list[int], list[float]]:
    rows_a = payload["raw_seed_metrics"][model_a]
    rows_b = payload["raw_seed_metrics"][model_b]
    seeds = sorted(set(map(int, rows_a)).intersection(map(int, rows_b)))
    differences = [
        float(rows_a[str(seed)][metric]) - float(rows_b[str(seed)][metric])
        for seed in seeds
    ]
    return seeds, differences


def svg_trace(payload: dict, destination: Path) -> None:
    signals = payload["signals"]
    times = [float(value) for value in signals["timesteps"]]
    series = [("Ground truth", "#111827", signals["ground_truth"]),
              ("T-FNO", "#2563eb", signals["tfno"]),
              ("U-Net", "#dc2626", signals["unet"])]
    width, height = 960, 560
    left, right, top, bottom = 90, 30, 55, 75
    values = [float(value) for _, _, rows in series for value in rows]
    y_min, y_max = min(values), max(values)
    pad = 0.05 * (y_max - y_min or 1.0)
    y_min, y_max = y_min - pad, y_max + pad

    def x(value: float) -> float:
        return left + (value - min(times)) / (max(times) - min(times)) * (width - left - right)

    def y(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * (height - top - bottom)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#111827}.axis{stroke:#111827;stroke-width:1.5}.grid{stroke:#d1d5db;stroke-width:1}</style>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="19">Tutorial Twall-100 dry-area fraction rollout</text>',
    ]
    for index in range(6):
        value = y_min + index * (y_max - y_min) / 5
        yy = y(value)
        parts.append(f'<line class="grid" x1="{left}" x2="{width-right}" y1="{yy:.2f}" y2="{yy:.2f}"/>')
        parts.append(f'<text x="{left-12}" y="{yy+5:.2f}" text-anchor="end" font-size="13">{value:.2f}</text>')
    parts.extend([
        f'<line class="axis" x1="{left}" x2="{width-right}" y1="{height-bottom}" y2="{height-bottom}"/>',
        f'<line class="axis" x1="{left}" x2="{left}" y1="{top}" y2="{height-bottom}"/>',
        f'<text x="{(left+width-right)/2}" y="{height-24}" text-anchor="middle" font-size="15">Source timestep</text>',
        f'<text x="20" y="{(top+height-bottom)/2}" text-anchor="middle" font-size="15" transform="rotate(-90 20 {(top+height-bottom)/2})">Dry-area fraction</text>',
    ])
    for name, color, rows in series:
        points = " ".join(f"{x(t):.2f},{y(float(value)):.2f}" for t, value in zip(times, rows, strict=True))
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2"/>')
    legend_x = width - 220
    for index, (name, color, _) in enumerate(series):
        yy = top + 22 * index
        parts.append(f'<line x1="{legend_x}" x2="{legend_x+30}" y1="{yy}" y2="{yy}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x+40}" y="{yy+5}" font-size="13">{html.escape(name)}</text>')
    parts.append('</svg>')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("reproduced"))
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir

    tutorial = load("benchmark_results/resolution_control_48x48/benchmark_results.json")
    archived = tutorial["pairwise_model_minus_unet"]["tfno"]
    expected = {
        "gwrmse": (0.004597402792413325, -0.05759044812328926, 0.05894272413430517, 0.890625, 1.0),
        "interface_temperature_rmse": (-0.18853127198476083, -0.47490005109236993, 0.0673182505738479, 0.234375, 1.0),
        "interface_temperature_jump_mae": (-0.09276868238156427, -0.2203219094991548, 0.025479007160725896, 0.1962890625, 1.0),
        "mass_conservation_mae": (0.049172396212384825, 0.04447743574313748, 0.053855332934945294, 0.0009765625, 0.021484375),
    }
    lines = ["Canonical CUDA 48x48 tutorial split (T-FNO minus U-Net; lower error is better):"]
    for metric, target in expected.items():
        seeds, differences = paired_values(tutorial, "tfno", "unet", metric)
        if len(seeds) != 11:
            raise AssertionError(f"{metric}: expected 11 paired seeds, found {len(seeds)}")
        mean = fmean(differences)
        p_value = exact_two_sided_sign_flip(differences)
        row = archived[metric]
        assert_close(f"{metric} mean", mean, target[0])
        assert_close(f"{metric} archived CI low", float(row["ci95_low"]), target[1])
        assert_close(f"{metric} archived CI high", float(row["ci95_high"]), target[2])
        assert_close(f"{metric} exact p", p_value, target[3])
        assert_close(f"{metric} Holm p", float(row["holm_bonferroni_p"]), target[4])
        lines.append(f"  {metric}: mean={mean:+.8f}, CI=[{target[1]:+.8f}, {target[2]:+.8f}], p={p_value:.9f}, Holm={target[4]:.8f}")

    divergence = load("audit/kaggle_hybrid_cuda_rerun_2026-08-14/hybrid_cuda_rerun/benchmark_results/benchmark_results.json")
    noninferiority = load("audit/kaggle_hybrid_cuda_rerun_2026-08-14/hybrid_cuda_rerun/divergence_noninferiority.json")
    seeds, differences = paired_values(divergence, "hybrid_div", "unet", "mass_conservation_mae")
    margin = float(noninferiority["protocol"]["margin"])
    shifted = [value - margin for value in differences]
    p_value = exact_lower_sign_flip(shifted)
    result = noninferiority["result"]
    assert_close("divergence mean", fmean(differences), -0.0703428772121202)
    assert_close("divergence hybrid mean", fmean(float(divergence["raw_seed_metrics"]["hybrid_div"][str(seed)]["mass_conservation_mae"]) for seed in seeds), 0.09527721242212324)
    assert_close("U-Net mean", fmean(float(divergence["raw_seed_metrics"]["unet"][str(seed)]["mass_conservation_mae"]) for seed in seeds), 0.16562008963424343)
    assert_close("non-inferiority p", p_value, 0.00048828125)
    assert_close("archived NI CI low", float(result["paired_bootstrap_ci95_low"]), -0.07454106214785754)
    assert_close("archived NI CI high", float(result["paired_bootstrap_ci95_high"]), -0.06653817410936194)
    if result["noninferior"] is not True:
        raise AssertionError("archived non-inferiority decision is not true")
    lines.extend([
        "Divergence hybrid (lambda_div=0.30) versus U-Net mass conservation:",
        f"  hybrid mean=0.09527721, U-Net mean=0.16562009, difference={fmean(differences):+.8f}",
        f"  archived CI=[-0.07454106, -0.06653817], exact one-sided p={p_value:.9f}, noninferior=True",
    ])

    rollout = load("benchmark_results/phase4_chf_rollout/rollout_results.json")
    figure = output_dir / "fig2_dry_area_trace.svg"
    svg_trace(rollout, figure)
    lines.extend([f"Figure reproduced: {figure.relative_to(ROOT)}", "PASS"])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "selftest_results.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
