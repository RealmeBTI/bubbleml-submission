import json, itertools, pathlib, datetime
from statistics import fmean

REPO   = pathlib.Path("/Users/sbmahafujbondhon/antigravity_BUbbleML/bubbleml-submission")

ref48_path = REPO / "benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_results.json"
ref96_path = REPO / "benchmark_results/resolution_control_96x96/benchmark_results.json"

if not ref48_path.exists():
    print("Missing ref48:", ref48_path)
if not ref96_path.exists():
    print("Missing ref96:", ref96_path)

ref48 = json.loads(ref48_path.read_text())
ref96 = json.loads(ref96_path.read_text())

METRICS = [
    "gwrmse",
    "interface_temperature_rmse",
    "interface_temperature_jump_mae",
    "mass_conservation_mae",
]

def exact_two_sided_sign_flip(differences):
    observed = abs(fmean(differences))
    distribution = (
        abs(fmean(s * d for s, d in zip(signs, differences, strict=True)))
        for signs in itertools.product((-1.0, 1.0), repeat=len(differences))
    )
    count = sum(v >= observed - 1e-15 for v in distribution)
    return count / (2 ** len(differences))

def paired_values(payload, model_a, model_b, metric):
    rows_a = payload["raw_seed_metrics"][model_a]
    rows_b = payload["raw_seed_metrics"][model_b]
    seeds  = sorted(set(map(int, rows_a)).intersection(map(int, rows_b)))
    diffs  = [float(rows_a[str(s)][metric]) - float(rows_b[str(s)][metric]) for s in seeds]
    return seeds, diffs

def holm_bonferroni(pairs):
    indexed = sorted(enumerate(pairs), key=lambda x: x[1][1])
    n = len(indexed)
    adjusted, running_max = [None] * n, 0.0
    for rank, (orig_idx, (metric, p)) in enumerate(indexed):
        adj = min(1.0, max(running_max, (n - rank) * p))
        running_max = adj
        adjusted[orig_idx] = (metric, adj)
    return dict(adjusted)

raw_ps = []
results_48, results_96 = {}, {}
for metric in METRICS:
    s48, d48 = paired_values(ref48, "tfno", "unet", metric)
    s96, d96 = paired_values(ref96, "tfno", "unet", metric)
    p48 = exact_two_sided_sign_flip(d48)
    p96 = exact_two_sided_sign_flip(d96)
    results_48[metric] = (s48, d48, p48)
    results_96[metric] = (s96, d96, p96)
    raw_ps.append((metric, p96))

holm_96 = holm_bonferroni(raw_ps)

print("=" * 70)
print("RESOLUTION CONTROL: 48x48 (n=11) vs 96x96 (n=7)")
print("T-FNO minus U-Net  |  negative = T-FNO better  |  lower error = better")
print("=" * 70)

all_results = []
for metric in METRICS:
    s48, d48, p48 = results_48[metric]
    s96, d96, p96 = results_96[metric]
    m48, m96 = fmean(d48), fmean(d96)
    # FIX: holm_96 is a dict mapping metric to adj_p
    holm96 = holm_96[metric]
    sign_consistent = (m48 < 0) == (m96 < 0)
    if p96 >= 0.10:
        verdict = "INCONCLUSIVE (p>=0.10 at 96x96)"
    elif sign_consistent:
        verdict = "HOLDS"
    else:
        verdict = "REVERSES"
    print()
    print(metric + ":")
    print("  48x48 (n=%d): mean=%+.6e  p=%.6f" % (len(s48), m48, p48))
    print("  96x96 (n=%d): mean=%+.6e  p=%.6f  Holm=%.6f" % (len(s96), m96, p96, holm96))
    print("  -> Ranking: " + verdict)
    all_results.append((metric, m96, p96, holm96, verdict))

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
for metric, mean, p, holm, verdict in all_results:
    print("  %-44s %s" % (metric, verdict))

summary = {
    "analysis_timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
    "comparison": "tfno_minus_unet",
    "description": (
        "Resolution-control: 48x48 (n=11) vs 96x96 (n=7), same tutorial-split "
        "conditions (Twall-103/106/100). Assesses whether T-FNO/U-Net ranking "
        "holds, reverses, or is inconclusive when resolution is the sole factor."
    ),
    "per_metric": {
        metric: {
            "mean_48x48": fmean(results_48[metric][1]),
            "n_48x48": len(results_48[metric][0]),
            "p_48x48_exact_sign_flip": results_48[metric][2],
            "mean_96x96": mean,
            "n_96x96": len(results_96[metric][0]),
            "p_96x96_exact_sign_flip": p,
            "holm_bonferroni_96x96": holm,
            "verdict": verdict,
        }
        for metric, mean, p, holm, verdict in all_results
    },
}
out_path = REPO / "benchmark_results/resolution_control_96x96/resolution_control_analysis.json"
out_path.write_text(json.dumps(summary, indent=2) + "\n")
print()
print("Analysis JSON written:", out_path)
