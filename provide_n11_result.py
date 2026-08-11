import json
import subprocess
import itertools
from statistics import fmean
import os

def exact_two_sided_sign_flip(differences):
    observed = abs(fmean(differences))
    distribution = (
        abs(fmean(s * d for s, d in zip(signs, differences, strict=True)))
        for signs in itertools.product((-1.0, 1.0), repeat=len(differences))
    )
    count = sum(v >= observed - 1e-15 for v in distribution)
    return count / (2 ** len(differences))

out = subprocess.check_output(["git", "show", "fd4142a79d51ef867795bc3f8c74bf3ee09c110a:benchmark_results/resolution_control_96x96/benchmark_results.json"])
res_4 = json.loads(out)
with open("benchmark_results/resolution_control_96x96/benchmark_results.json", "r") as f:
    res_7 = json.load(f)

tfno_metrics = {}
unet_metrics = {}
for seed, m in res_7["raw_seed_metrics"]["tfno"].items(): tfno_metrics[seed] = m
for seed, m in res_7["raw_seed_metrics"]["unet"].items(): unet_metrics[seed] = m
for seed, m in res_4["raw_seed_metrics"]["tfno"].items(): tfno_metrics[seed] = m
for seed, m in res_4["raw_seed_metrics"]["unet"].items(): unet_metrics[seed] = m

with open("benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_results.json", "r") as f:
    res_48 = json.load(f)

metrics = ["gwrmse", "interface_temperature_rmse", "interface_temperature_jump_mae", "mass_conservation_mae"]

p_48 = {}
mean_48 = {}
for metric in metrics:
    seeds_48 = sorted(res_48["raw_seed_metrics"]["tfno"].keys(), key=int)
    tfno_48 = [float(res_48["raw_seed_metrics"]["tfno"][s][metric]) for s in seeds_48]
    unet_48 = [float(res_48["raw_seed_metrics"]["unet"][s][metric]) for s in seeds_48]
    diffs_48 = [t - u for t, u in zip(tfno_48, unet_48)]
    mean_48[metric] = fmean(diffs_48)
    p_48[metric] = exact_two_sided_sign_flip(diffs_48)

seeds_96 = sorted(tfno_metrics.keys(), key=int)
p_96 = {}
diffs_96_all = {}
for metric in metrics:
    tfno_96 = [float(tfno_metrics[s][metric]) for s in seeds_96]
    unet_96 = [float(unet_metrics[s][metric]) for s in seeds_96]
    diffs_96 = [t - u for t, u in zip(tfno_96, unet_96)]
    diffs_96_all[metric] = diffs_96
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

print("======================================================================")
print("RESOLUTION CONTROL: 48x48 (n=11) vs 96x96 (n=11)")
print("T-FNO minus U-Net  |  negative = T-FNO better  |  lower error = better")
print("======================================================================\n")
for metric in metrics:
    print(f"{metric}:")
    m48 = mean_48[metric]
    m96 = fmean(diffs_96_all[metric])
    p48 = p_48[metric]
    p96 = p_96[metric]
    h96 = holm_96[metric]
    
    print(f"  48x48 (n=11): mean={m48:+.6e}  p={p48:.6f}")
    print(f"  96x96 (n=11): mean={m96:+.6e}  p={p96:.6f}  Holm={h96:.6f}")
    
    if p48 < 0.05 and h96 < 0.05:
        if (m48 < 0 and m96 > 0) or (m48 > 0 and m96 < 0):
            print("  -> Ranking: REVERSES (Both significant, but opposite signs)")
        else:
            print("  -> Ranking: HOLDS (Both significant, same sign)")
    elif p48 >= 0.05 and h96 < 0.05:
        print("  -> Ranking: REVERSES (Inconclusive at 48x48, definitive at 96x96)")
    elif p48 < 0.05 and h96 >= 0.05:
        print("  -> Ranking: REVERSES (Definitive at 48x48, inconclusive at 96x96)")
    else:
        print("  -> Ranking: HOLDS (Inconclusive at both resolutions)")
    print("")
