import json
import subprocess
import itertools
from statistics import fmean, stdev
import numpy as np
import os
import csv

def exact_two_sided_sign_flip(differences):
    observed = abs(fmean(differences))
    distribution = (
        abs(fmean(s * d for s, d in zip(signs, differences, strict=True)))
        for signs in itertools.product((-1.0, 1.0), repeat=len(differences))
    )
    count = sum(v >= observed - 1e-15 for v in distribution)
    return count / (2 ** len(differences))

# 1. Load the 4 seeds from fd4142a
out = subprocess.check_output(["git", "show", "fd4142a79d51ef867795bc3f8c74bf3ee09c110a:benchmark_results/resolution_control_96x96/benchmark_results.json"])
res_4 = json.loads(out)

# 2. Load current benchmark_results.json (n=7)
with open("benchmark_results/resolution_control_96x96/benchmark_results.json", "r") as f:
    res = json.load(f)

# 3. Merge raw_seed_metrics
for model in ["tfno", "unet"]:
    for seed, metrics in res_4["raw_seed_metrics"][model].items():
        res["raw_seed_metrics"][model][seed] = metrics

# 4. Recompute aggregates
METRICS = ["gwrmse", "interface_temperature_rmse", "interface_temperature_jump_mae", "mass_conservation_mae"]
for model in ["tfno", "unet"]:
    for metric in res["raw_seed_metrics"][model][list(res["raw_seed_metrics"][model].keys())[0]].keys():
        if type(res["raw_seed_metrics"][model][list(res["raw_seed_metrics"][model].keys())[0]][metric]) in [int, float, str]:
            try:
                vals = [float(v[metric]) for v in res["raw_seed_metrics"][model].values()]
                mean = np.mean(vals)
                std = np.std(vals, ddof=1) if len(vals) > 1 else 0
                res["aggregate"][model][metric] = f"{mean:.4e} +/- {std:.4e}"
            except ValueError:
                pass # skip non-numeric like device strings

# 5. Recompute pairwise for n=11
res["pairwise_model_minus_unet"]["tfno"] = {}
seeds = sorted(res["raw_seed_metrics"]["tfno"].keys(), key=int)
for metric in METRICS:
    tfno_vals = [float(res["raw_seed_metrics"]["tfno"][s][metric]) for s in seeds]
    unet_vals = [float(res["raw_seed_metrics"]["unet"][s][metric]) for s in seeds]
    diffs = [t - u for t, u in zip(tfno_vals, unet_vals)]
    mean_diff = fmean(diffs)
    p = exact_two_sided_sign_flip(diffs)
    
    # Bootstrapped CI
    np.random.seed(42)
    boot_means = []
    for _ in range(10000):
        sample = np.random.choice(diffs, size=len(diffs), replace=True)
        boot_means.append(np.mean(sample))
    ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])
    
    res["pairwise_model_minus_unet"]["tfno"][metric] = {
        "mean_fno_minus_unet": mean_diff,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "paired_sign_flip_p": p
    }

# Save updated JSON
with open("benchmark_results/resolution_control_96x96/benchmark_results.json", "w") as f:
    json.dump(res, f, indent=2)

# 6. Generate CSV
csv_rows = []
csv_rows.append(["model", "seed", "metric", "value"])
for model in ["tfno", "unet"]:
    for seed, metrics in res["raw_seed_metrics"][model].items():
        for k, v in metrics.items():
            csv_rows.append([model, seed, k, v])

with open("benchmark_results/resolution_control_96x96/benchmark_summary.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerows(csv_rows)

# 7. Generate resolution_control_analysis.json (Comparing n=11 to n=11)
with open("benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_results.json", "r") as f:
    res_48 = json.load(f)

p_48 = {}
mean_48 = {}
for metric in METRICS:
    seeds_48 = sorted(res_48["raw_seed_metrics"]["tfno"].keys(), key=int)
    tfno_48 = [float(res_48["raw_seed_metrics"]["tfno"][s][metric]) for s in seeds_48]
    unet_48 = [float(res_48["raw_seed_metrics"]["unet"][s][metric]) for s in seeds_48]
    diffs_48 = [t - u for t, u in zip(tfno_48, unet_48)]
    mean_48[metric] = fmean(diffs_48)
    p_48[metric] = exact_two_sided_sign_flip(diffs_48)

p_96 = {}
mean_96 = {}
for metric in METRICS:
    tfno_96 = [float(res["raw_seed_metrics"]["tfno"][s][metric]) for s in seeds]
    unet_96 = [float(res["raw_seed_metrics"]["unet"][s][metric]) for s in seeds]
    diffs_96 = [t - u for t, u in zip(tfno_96, unet_96)]
    mean_96[metric] = fmean(diffs_96)
    p_96[metric] = exact_two_sided_sign_flip(diffs_96)

sorted_p = sorted(p_96.items(), key=lambda x: x[1])
holm_96 = {}
m_count = len(sorted_p)
for i, (metric, pval) in enumerate(sorted_p):
    adjusted = min(1.0, pval * (m_count - i))
    if i > 0:
        prev_adjusted = holm_96[sorted_p[i-1][0]]
        adjusted = max(prev_adjusted, adjusted)
    holm_96[metric] = adjusted

import datetime
analysis = {
    "analysis_timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
    "comparison": "tfno_minus_unet",
    "description": "Resolution-control: 48x48 (n=11) vs 96x96 (n=11), same tutorial-split conditions (Twall-103/106/100). Assesses whether T-FNO/U-Net ranking holds, reverses, or is inconclusive when resolution is the sole factor.",
    "per_metric": {}
}

for metric in METRICS:
    p48 = p_48[metric]
    h96 = holm_96[metric]
    m48 = mean_48[metric]
    m96 = mean_96[metric]
    
    if p48 < 0.05 and h96 < 0.05:
        if (m48 < 0 and m96 > 0) or (m48 > 0 and m96 < 0):
            verdict = "REVERSES (Both significant, but opposite signs)"
        else:
            verdict = "HOLDS (Both significant, same sign)"
    elif p48 >= 0.05 and h96 < 0.05:
        verdict = "REVERSES (Inconclusive at 48x48, definitive at 96x96)"
    elif p48 < 0.05 and h96 >= 0.05:
        verdict = "REVERSES (Definitive at 48x48, inconclusive at 96x96)"
    else:
        verdict = "HOLDS (Inconclusive at both resolutions)"
        
    analysis["per_metric"][metric] = {
        "mean_48x48": m48,
        "n_48x48": len(seeds_48),
        "p_48x48_exact_sign_flip": p48,
        "mean_96x96": m96,
        "n_96x96": len(seeds),
        "p_96x96_exact_sign_flip": p_96[metric],
        "holm_bonferroni_96x96": h96,
        "verdict": verdict
    }

with open("benchmark_results/resolution_control_96x96/resolution_control_analysis.json", "w") as f:
    json.dump(analysis, f, indent=2)

print("Merged results to n=11, re-computed CSV, and generated analysis JSON successfully!")
