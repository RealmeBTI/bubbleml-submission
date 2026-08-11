import json
import pathlib
import subprocess
import sys
from bubbleml_benchmark.paper_benchmark import run, PaperBenchmarkConfig

REPO = pathlib.Path("/Users/sbmahafujbondhon/antigravity_BUbbleML/bubbleml-submission")
BRES_96 = REPO / "benchmark_results/resolution_control_96x96/benchmark_results.json"
BRES_MISSING = pathlib.Path("/tmp/kaggle_missing_out_v2/bubbleml-submission/benchmark_results/resolution_control_96x96/benchmark_results.json")

# Load existing 7 seeds
with open(BRES_96, "r") as f:
    res96 = json.load(f)

# Load missing 4 seeds
with open(BRES_MISSING, "r") as f:
    res_missing = json.load(f)

# Merge raw_seed_metrics
for model in ["tfno", "unet"]:
    for seed, metrics in res_missing["raw_seed_metrics"][model].items():
        res96["raw_seed_metrics"][model][seed] = metrics

# To recompute aggregates, we can use the `run` method from paper_benchmark
# Wait, paper_benchmark.run expects checkpoints and runs inference. We DO NOT want to run inference.
# We just need to compute the aggregate and pairwise metrics from the raw_seed_metrics.

import numpy as np
from statistics import fmean, stdev

METRICS = ["gwrmse", "interface_temperature_rmse", "interface_temperature_jump_mae", "mass_conservation_mae"]

# Recompute aggregates
res96["aggregate"] = {}
for model in ["tfno", "unet"]:
    res96["aggregate"][model] = {}
    for metric in METRICS:
        vals = [float(v[metric]) for v in res96["raw_seed_metrics"][model].values()]
        mean = np.mean(vals)
        std = np.std(vals, ddof=1)
        res96["aggregate"][model][metric] = f"{mean:.4e} +/- {std:.4e}"

# Recompute pairwise tfno minus unet
from scipy.stats import wilcoxon
import itertools
def exact_two_sided_sign_flip(differences):
    observed = abs(fmean(differences))
    distribution = (
        abs(fmean(s * d for s, d in zip(signs, differences, strict=True)))
        for signs in itertools.product((-1.0, 1.0), repeat=len(differences))
    )
    count = sum(v >= observed - 1e-15 for v in distribution)
    return count / (2 ** len(differences))

res96["pairwise_model_minus_unet"] = {"tfno": {}}
seeds = sorted(res96["raw_seed_metrics"]["tfno"].keys(), key=int)
for metric in METRICS:
    tfno_vals = [float(res96["raw_seed_metrics"]["tfno"][s][metric]) for s in seeds]
    unet_vals = [float(res96["raw_seed_metrics"]["unet"][s][metric]) for s in seeds]
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
    
    res96["pairwise_model_minus_unet"]["tfno"][metric] = {
        "mean_fno_minus_unet": mean_diff,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "paired_sign_flip_p": p
    }

# Save updated JSON
with open(BRES_96, "w") as f:
    json.dump(res96, f, indent=2)

print("Merged results to n=11 successfully!")
