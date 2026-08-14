#!/usr/bin/env python3
"""Generate the numerical ledger for the canonical BubbleML manuscript.

Only four retained artifacts are eligible inputs:

* ``resolution_control_48x48``: the canonical, CUDA tutorial split;
* ``resolution_control_96x96``: an exploratory stored configuration; and
* ``multitraj96/report_summary.json``: the descriptive cross-condition study;
* ``audit/kaggle_hybrid_cuda_rerun_2026-08-14/hybrid_cuda_rerun``: the
  checkpoint-retaining canonical CUDA intervention rerun.

The retired MPS ``phase1_gpu_decisive_tfno_unet_n11`` result is deliberately
not read.  This script re-computes paired tutorial and 96x96 statistics from
per-seed data, pins the bootstrap generator to seed 123, and validates the
stored comparisons before writing machine-readable and reviewer-readable
outputs.  Cross-condition per-seed values are not retained; its reported
summary is therefore copied as a labelled stored summary rather than being
recomputed or represented as a new calculation.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from statistics import fmean
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 123
PRIMARY_METRICS = (
    "gwrmse",
    "interface_temperature_rmse",
    "interface_temperature_jump_mae",
    "mass_conservation_mae",
)
COMPUTE_ONLY_METRICS = {
    "device",
    "latency_ms_per_sample",
    "latency_ms_per_window",
    "model_inference_latency_ms_per_window",
    "model_inference_throughput_windows_per_second",
    "parameters",
    "real_scalar_parameters",
    "throughput_fps",
    "throughput_windows_per_second",
}
METRIC_LABELS = {
    "gwrmse": "GWRMSE",
    "interface_temperature_rmse": "Interface-temperature RMSE",
    "interface_temperature_jump_mae": "Interface-temperature-jump MAE",
    "mass_conservation_mae": "Mass-conservation MAE",
}


def load(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def bootstrap_ci(values: np.ndarray) -> tuple[float, float]:
    """Match ``bubbleml_benchmark.benchmark._bootstrap_ci`` exactly."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = rng.choice(values, size=(BOOTSTRAP_SAMPLES, len(values)), replace=True).mean(axis=1)
    low, high = np.quantile(means, (0.025, 0.975))
    return float(low), float(high)


def exact_sign_flip_pvalue(values: np.ndarray) -> float:
    """Match the exact two-sided enumeration used by the benchmark."""
    observed = abs(float(values.mean()))
    distribution = np.fromiter(
        (abs(float((np.asarray(signs) * values).mean()))
         for signs in itertools.product((-1.0, 1.0), repeat=len(values))),
        dtype=float,
    )
    return float(np.count_nonzero(distribution >= observed) / len(distribution))


def exact_lower_sign_flip_pvalue(values: np.ndarray) -> float:
    """Exact one-sided lower-tail sign-flip test used by the frozen gate."""
    observed = float(values.mean())
    distribution = np.fromiter(
        (float((np.asarray(signs) * values).mean())
         for signs in itertools.product((-1.0, 1.0), repeat=len(values))),
        dtype=float,
    )
    return float(np.count_nonzero(distribution <= observed + 1e-15) / len(distribution))


def holm(rows: dict[str, dict[str, float]]) -> None:
    previous = 0.0
    ordered = sorted(rows.items(), key=lambda item: item[1]["exact_p"])
    for rank, (_, row) in enumerate(ordered):
        adjusted = min(1.0, max(previous, (len(ordered) - rank) * row["exact_p"]))
        row["holm_p"] = adjusted
        previous = adjusted


def assert_close(label: str, actual: float, expected: float, tolerance: float = 5e-12) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance):
        raise RuntimeError(f"{label}: recomputed {actual:.17g}, stored {expected:.17g}")


def paired_arm(relative: str, name: str, *, require_stored_ci_match: bool) -> dict[str, Any]:
    payload = load(relative)
    raw = payload["raw_seed_metrics"]
    if set(raw) != {"tfno", "unet"}:
        raise RuntimeError(f"{relative}: expected only tfno/unet raw seed metrics.")
    seeds = sorted(set(map(int, raw["tfno"])).intersection(map(int, raw["unet"])))
    if len(seeds) != 11:
        raise RuntimeError(f"{relative}: expected 11 paired seeds, found {seeds}.")
    stored = payload["pairwise_model_minus_unet"]["tfno"]
    all_results: dict[str, dict[str, float]] = {}
    means: dict[str, dict[str, float]] = {}
    metric_names = sorted(
        set.intersection(*(set(raw[model][str(seed)]) for model in ("tfno", "unet") for seed in seeds))
    )
    verification_failures: list[str] = []
    for metric in metric_names:
        if metric in COMPUTE_ONLY_METRICS:
            continue
        tfno = np.asarray([float(raw["tfno"][str(seed)][metric]) for seed in seeds])
        unet = np.asarray([float(raw["unet"][str(seed)][metric]) for seed in seeds])
        difference = tfno - unet
        low, high = bootstrap_ci(difference)
        row = {
            "mean_tfno_minus_unet": float(difference.mean()),
            "ci95_low": low,
            "ci95_high": high,
            "exact_p": exact_sign_flip_pvalue(difference),
        }
        if metric in stored:
            stored_row = stored[metric]
            assert_close(f"{name} {metric} mean", row["mean_tfno_minus_unet"], float(stored_row["mean_fno_minus_unet"]))
            assert_close(f"{name} {metric} exact p", row["exact_p"], float(stored_row["paired_sign_flip_p"]))
            for bound in ("ci95_low", "ci95_high"):
                try:
                    assert_close(f"{name} {metric} {bound}", row[bound], float(stored_row[bound]))
                except RuntimeError as error:
                    if require_stored_ci_match:
                        raise
                    verification_failures.append(str(error))
        all_results[metric] = row
        if metric in PRIMARY_METRICS:
            means[metric] = {"tfno": float(tfno.mean()), "unet": float(unet.mean())}
    holm(all_results)
    for metric, row in all_results.items():
        if metric not in stored:
            continue
        stored_holm = stored[metric].get("holm_bonferroni_p")
        # The 96x96 legacy output omits this field; its complete-metric family
        # correction is regenerated here from all retained error metrics below.
        if stored_holm is not None:
            assert_close(f"{name} {metric} stored Holm", row["holm_p"], float(stored_holm))
    return {
        "artifact": relative,
        "commit": payload["metadata"].get("checkpoint_git_commits", []),
        "device": payload["metadata"].get("device"),
        "seeds": seeds,
        "bootstrap": {"samples": BOOTSTRAP_SAMPLES, "rng_seed": BOOTSTRAP_SEED},
        "stored_ci_verification": "PASS" if not verification_failures else "BLOCKED",
        "stored_ci_verification_failures": verification_failures,
        "means": means,
        "tfno_minus_unet": {metric: all_results[metric] for metric in PRIMARY_METRICS},
    }


def cross_condition() -> dict[str, Any]:
    payload = load("benchmark_results/multitraj96/report_summary.json")
    if payload.get("status") != "complete":
        raise RuntimeError("Cross-condition summary is not marked complete.")
    if len(payload.get("seeds", [])) != 5:
        raise RuntimeError("Cross-condition summary does not contain the frozen five-seed design.")
    retained_models = {"tfno", "unet"}
    if not retained_models.issubset(payload.get("means", {})):
        raise RuntimeError("Cross-condition summary lacks the retained T-FNO/U-Net comparison.")
    excluded_models = sorted(set(payload["means"]) - retained_models)
    return {
        "artifact": "benchmark_results/multitraj96/report_summary.json",
        "source_status": (
            "stored T-FNO/U-Net summary; per-seed metrics are not retained locally; "
            "retired-pipeline intervention fields in the source artifact are excluded"
        ),
        "excluded_stored_models": excluded_models,
        "archive_sha256": payload["archive_sha256"],
        "device": payload["device"],
        "resolution": payload["resolution"],
        "seeds": payload["seeds"],
        "split": payload["split"],
        "means": {
            model: {metric: float(value) for metric, value in payload["means"][model].items()}
            for model in ("tfno", "unet")
        },
        "tfno_minus_unet": {
            metric: {
                "mean_tfno_minus_unet": float(row["mean"]),
                "ci95_low": float(row["ci95"][0]),
                "ci95_high": float(row["ci95"][1]),
                "exact_p": float(row["exact_p"]),
                "holm_p": float(row["holm_p"]),
            }
            for metric, row in payload["tfno_minus_unet"].items()
            if metric in PRIMARY_METRICS
        },
    }


def hybrid_cuda_intervention() -> dict[str, Any]:
    """Validate and summarize the checkpoint-retaining CUDA intervention run."""
    base = "audit/kaggle_hybrid_cuda_rerun_2026-08-14/hybrid_cuda_rerun"
    benchmark = load(f"{base}/benchmark_results/benchmark_results.json")
    hybrid_gate = load(f"{base}/hybrid_noninferiority.json")
    divergence_gate = load(f"{base}/divergence_noninferiority.json")
    hardware = load(f"{base}/hardware.json")
    if not hardware.get("cuda_available") or not hardware.get("gpus"):
        raise RuntimeError("Hybrid intervention artifact is not a CUDA run.")
    if any(gpu.get("name") != "Tesla T4" for gpu in hardware["gpus"]):
        raise RuntimeError("Hybrid intervention artifact does not report the audited Tesla T4 runtime.")

    raw = benchmark["raw_seed_metrics"]
    expected_models = {"tfno", "unet", "hybrid_tfno", "hybrid_div"}
    if set(raw) != expected_models:
        raise RuntimeError(f"Hybrid intervention models differ from the frozen set: {sorted(raw)}")
    seeds = sorted(set.intersection(*(set(map(int, raw[model])) for model in expected_models)))
    if len(seeds) != 11:
        raise RuntimeError(f"Hybrid intervention expected 11 paired seeds, found {seeds}.")

    # The rerun re-evaluated the immutable baseline checkpoints.  Equality
    # against the canonical tutorial artifact prevents a silent data/split drift.
    tutorial = load("benchmark_results/resolution_control_48x48/benchmark_results.json")
    for model in ("tfno", "unet"):
        for seed in seeds:
            rerun_row = raw[model][str(seed)]
            tutorial_row = tutorial["raw_seed_metrics"][model][str(seed)]
            for metric in set(rerun_row).intersection(tutorial_row) - COMPUTE_ONLY_METRICS:
                assert_close(
                    f"hybrid rerun baseline {model} seed {seed} {metric}",
                    float(rerun_row[metric]),
                    float(tutorial_row[metric]),
                    tolerance=5e-8,
                )

    metric = "mass_conservation_mae"
    differences = np.asarray([
        float(raw["hybrid_div"][str(seed)][metric]) - float(raw["unet"][str(seed)][metric])
        for seed in seeds
    ])
    result = divergence_gate["result"]
    margin = float(divergence_gate["protocol"]["margin"])
    low, high = bootstrap_ci(differences)
    one_sided_p = exact_lower_sign_flip_pvalue(differences - margin)
    assert_close("hybrid divergence mean", float(differences.mean()), float(result["mean_hybrid_div_minus_unet"]))
    assert_close("hybrid divergence CI low", low, float(result["paired_bootstrap_ci95_low"]))
    assert_close("hybrid divergence CI high", high, float(result["paired_bootstrap_ci95_high"]))
    assert_close("hybrid divergence one-sided p", one_sided_p, float(result["noninferiority_sign_flip_p"]))
    if result.get("noninferior") is not True:
        raise RuntimeError("Fresh CUDA divergence intervention did not pass its frozen gate.")

    zero = hybrid_gate["tests"]
    return {
        "artifact": f"{base}/benchmark_results/benchmark_results.json",
        "gate_artifacts": [f"{base}/hybrid_noninferiority.json", f"{base}/divergence_noninferiority.json"],
        "checkpoint_commit": benchmark["metadata"].get("checkpoint_git_commits", []),
        "device": benchmark["metadata"].get("device"),
        "runtime": hardware,
        "seeds": seeds,
        "baseline_identity": "PASS",
        "zero_penalty": zero,
        "divergence": {
            "lambda_div": 0.30,
            "hybrid_mean": float(np.mean([float(raw["hybrid_div"][str(seed)][metric]) for seed in seeds])),
            "unet_mean": float(np.mean([float(raw["unet"][str(seed)][metric]) for seed in seeds])),
            "mean_hybrid_minus_unet": float(differences.mean()),
            "ci95_low": low,
            "ci95_high": high,
            "margin": margin,
            "one_sided_exact_p": one_sided_p,
            "holm_p": float(result["holm_noninferiority_p"]),
            "noninferior": True,
        },
    }


def build_ledger() -> dict[str, Any]:
    return {
        "canonical_tutorial": paired_arm(
            "benchmark_results/resolution_control_48x48/benchmark_results.json", "canonical tutorial 48x48",
            require_stored_ci_match=True,
        ),
        "exploratory_96x96": paired_arm(
            "benchmark_results/resolution_control_96x96/benchmark_results.json", "exploratory 96x96",
            require_stored_ci_match=False,
        ),
        "cross_condition": cross_condition(),
        "hybrid_cuda_intervention": hybrid_cuda_intervention(),
    }


def signed(value: float, digits: int = 5) -> str:
    return f"{value:+.{digits}f}"


def pvalue(value: float) -> str:
    return f"{value:.6g}".replace("0.", ".")


def manuscript_fragments(ledger: dict[str, Any]) -> dict[str, str]:
    """Return Markdown blocks inserted by the LaTeX builder, never hand-typed."""
    tutorial = ledger["canonical_tutorial"]["tfno_minus_unet"]
    t_g = tutorial["gwrmse"]
    t_i = tutorial["interface_temperature_rmse"]
    t_j = tutorial["interface_temperature_jump_mae"]
    t_m = tutorial["mass_conservation_mae"]
    tutorial_results = (
        f"Across 11 paired seeds, T-FNO was significantly worse on mass-conservation MAE "
        f"({signed(t_m['mean_tfno_minus_unet'])}, 95% paired bootstrap CI "
        f"[{signed(t_m['ci95_low'])}, {signed(t_m['ci95_high'])}], unadjusted p={pvalue(t_m['exact_p'])}, "
        f"Holm p={pvalue(t_m['holm_p'])}). No overall GWRMSE winner was established "
        f"(T-FNO − U-Net: {signed(t_g['mean_tfno_minus_unet'])}, 95% paired bootstrap CI "
        f"[{signed(t_g['ci95_low'])}, {signed(t_g['ci95_high'])}], sign-flip p={pvalue(t_g['exact_p'])}, "
        f"Holm p={pvalue(t_g['holm_p'])}). T-FNO showed no statistically significant advantage on "
        f"interface-temperature RMSE ({signed(t_i['mean_tfno_minus_unet'])}, 95% CI "
        f"[{signed(t_i['ci95_low'])}, {signed(t_i['ci95_high'])}], unadjusted p={pvalue(t_i['exact_p'])}, "
        f"Holm p={pvalue(t_i['holm_p'])}) or interface-temperature-jump MAE "
        f"({signed(t_j['mean_tfno_minus_unet'])}, 95% CI [{signed(t_j['ci95_low'])}, "
        f"{signed(t_j['ci95_high'])}], unadjusted p={pvalue(t_j['exact_p'])}, Holm p={pvalue(t_j['holm_p'])}). "
        "Thus, the fixed-split evidence supports a conservation weakness "
        "for T-FNO, without a confirmed offsetting interface-fidelity benefit."
    )
    intervention = ledger["hybrid_cuda_intervention"]
    zero = intervention["zero_penalty"]
    z_mass = zero["mass_conservation_mae"]
    z_rmse = zero["interface_temperature_rmse"]
    z_jump = zero["interface_temperature_jump_mae"]
    div = intervention["divergence"]
    hybrid_results = (
        "The checkpoint-retaining CUDA rerun used the same 11 paired seeds, prepared tensors, and immutable "
        "T-FNO/U-Net baseline checkpoints as Section 4.1; baseline-metric identity was verified before the "
        "intervention analysis. The zero-penalty local-global hybrid was non-inferior to T-FNO on "
        f"interface-temperature RMSE (Holm p={pvalue(z_rmse['holm_noninferiority_p'])}) and jump MAE "
        f"(Holm p={pvalue(z_jump['holm_noninferiority_p'])}), but failed mass-conservation non-inferiority "
        f"to U-Net (hybrid minus U-Net {signed(z_mass['mean_hybrid_minus_comparator'])}, 95% CI "
        f"[{signed(z_mass['paired_bootstrap_ci95_low'])}, {signed(z_mass['paired_bootstrap_ci95_high'])}], "
        f"Holm p={pvalue(z_mass['holm_noninferiority_p'])}). A local receptive field alone therefore did not "
        "recover U-Net's conservation behavior.\n\n"
        f"With the frozen $\\lambda_{{\\mathrm{{div}}}}={div['lambda_div']:.2f}$ intervention, the divergence "
        f"hybrid passed the predeclared one-metric mass-conservation non-inferiority gate: mean mass MAE "
        f"{div['hybrid_mean']:.5f} versus {div['unet_mean']:.5f} for U-Net, paired difference "
        f"${signed(div['mean_hybrid_minus_unet'])}$, 95% CI "
        f"$[{signed(div['ci95_low'])}, {signed(div['ci95_high'])}]$, exact one-sided "
        f"p={pvalue(div['one_sided_exact_p'])}. The fresh CUDA "
        "rerun did not establish an interface regression relative to the zero-penalty hybrid. This is a "
        "confirmatory tutorial-split result only; no divergence-hybrid numerical claim is made for the "
        "independent cross-condition split."
    )
    cross = ledger["cross_condition"]
    c = cross["tfno_minus_unet"]
    rows = []
    for model, label in (("tfno", "T-FNO"), ("unet", "**U-Net**")):
        if model in cross["means"]:
            values = cross["means"][model]
            rows.append("| " + label + " | " + " | ".join(f"{values[m]:.4f}" if m != "mass_conservation_mae" else f"{values[m]:.5f}" for m in PRIMARY_METRICS) + " |")
    cross_table = "\n".join([
        "| Model | GWRMSE | Interface-temperature RMSE | Interface-temperature-jump MAE | Mass-conservation MAE |",
        "|---|---:|---:|---:|---:|",
        *rows,
    ])
    cross_results = (
        "The locally retained cross-condition summary reports T-FNO minus U-Net as "
        + "; ".join(
            f"{METRIC_LABELS[m]} {signed(c[m]['mean_tfno_minus_unet'])} (95% CI "
            f"[{signed(c[m]['ci95_low'])}, {signed(c[m]['ci95_high'])}])" for m in PRIMARY_METRICS
        )
        + ". Every unadjusted exact two-sided p-value is .0625 (the minimum attainable at n=5) and every "
        "Holm-adjusted p-value is 1.0. The stored directions consistently favor U-Net, including on mass "
        "conservation, but this descriptive five-seed/two-trajectory check is statistically underpowered and "
        "does not establish a cross-condition ranking."
    )
    return {
        "tutorial_results": tutorial_results,
        "hybrid_results": hybrid_results,
        "cross_condition_table": cross_table,
        "cross_condition_results": cross_results,
        "exploratory_96x96_status": ledger["exploratory_96x96"]["stored_ci_verification"],
    }


def report(ledger: dict[str, Any]) -> str:
    lines = [
        "# Canonical numerical ledger",
        "",
        "Generated by `scripts/generate_canonical_statistics.py`; bootstrap uses 10,000 paired resamples and NumPy RNG seed 123.",
        "",
        "## Eligible inputs",
        "",
    ]
    for key in ("canonical_tutorial", "exploratory_96x96", "cross_condition", "hybrid_cuda_intervention"):
        entry = ledger[key]
        lines.append(f"- `{entry['artifact']}`")
    lines.extend(["", "## Recomputed paired results", ""])
    for label, key in (("Canonical 48×48 tutorial", "canonical_tutorial"), ("Exploratory 96×96", "exploratory_96x96")):
        entry = ledger[key]
        if entry["stored_ci_verification"] != "PASS":
            lines.extend([
                f"### {label}",
                "",
                "**BLOCKED:** stored paired confidence intervals do not reproduce from the retained eleven raw seed rows using the documented benchmark bootstrap procedure (10,000 resamples, NumPy RNG seed 123). This arm is not eligible for numerical manuscript reporting until its analysis provenance is reconciled.",
                "",
                *[f"- {failure}" for failure in entry["stored_ci_verification_failures"]],
                "",
            ])
            continue
        lines.extend([f"### {label}", "", "| Metric | T-FNO − U-Net | 95% CI | exact p | Holm p |", "|---|---:|---:|---:|---:|"])
        for metric, row in entry["tfno_minus_unet"].items():
            lines.append(f"| {METRIC_LABELS[metric]} | {signed(row['mean_tfno_minus_unet'])} | [{signed(row['ci95_low'])}, {signed(row['ci95_high'])}] | {pvalue(row['exact_p'])} | {pvalue(row['holm_p'])} |")
        lines.append("")
    lines.extend([
        "## Cross-condition stored summary",
        "",
        "This section is transcribed from the compact retained summary, not recomputed, because the per-seed metrics are not locally retained.",
        "",
        manuscript_fragments(ledger)["cross_condition_table"],
        "",
        manuscript_fragments(ledger)["cross_condition_results"],
        "",
        "## Canonical CUDA intervention rerun",
        "",
        manuscript_fragments(ledger)["hybrid_results"],
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("manuscript/generated"))
    args = parser.parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    ledger = build_ledger()
    output.mkdir(parents=True, exist_ok=True)
    (output / "canonical_statistics.json").write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "canonical_fragments.json").write_text(json.dumps(manuscript_fragments(ledger), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "canonical_statistics.md").write_text(report(ledger), encoding="utf-8")
    print(output / "canonical_statistics.json")


if __name__ == "__main__":
    main()
