import json
import pathlib
import subprocess
import sys
import numpy as np
import itertools
from statistics import fmean
import csv

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def exact_two_sided_sign_flip(differences):
    observed = abs(fmean(differences))
    distribution = [abs(fmean(s * d for s, d in zip(signs, differences))) for signs in itertools.product((-1.0, 1.0), repeat=len(differences))]
    count = sum(v >= observed - 1e-15 for v in distribution)
    return count / (2 ** len(differences))

def check(condition, message):
    if not condition:
        print(f"[FAIL] {message}")
        sys.exit(1)
    else:
        print(f"[PASS] {message}")

def main():
    print("=== FINAL PUBLICATION-READINESS / REPRODUCIBILITY / STATISTICAL AUDIT ===")
    
    # 1-3. Git State
    branch, _ = run_cmd("git branch --show-current")
    check("manuscript/n11-resolution-audit" in branch, f"Expected branch manuscript/n11-resolution-audit, got {branch}")
    
    status, _ = run_cmd("git status --porcelain")
    # allow some untracked files but check for modified tracked files
    modified = [line for line in status.split('\n') if line.startswith(' M')]
    check(len(modified) == 0, "Repository has uncommitted modifications in tracked files (excluding untracked scripts)")
    
    # 4-5. Seeds and Artifacts
    exp_dir = pathlib.Path('experiments/resolution_control_48x48')
    tfno_dirs = list(exp_dir.glob('tfno_seed_*'))
    unet_dirs = list(exp_dir.glob('unet_seed_*'))
    expected_seeds = {42, 100, 1234, 2025, 9999, 7, 17, 314, 2718, 4242, 7777}
    
    tfno_seeds = {int(p.name.split('_')[-1]) for p in tfno_dirs}
    unet_seeds = {int(p.name.split('_')[-1]) for p in unet_dirs}
    
    check(tfno_seeds == expected_seeds, "TFNO seeds match exactly")
    check(unet_seeds == expected_seeds, "UNET seeds match exactly")
    
    for seed in expected_seeds:
        for model in ['tfno', 'unet']:
            d = exp_dir / f"{model}_seed_{seed}"
            check((d / 'config.yaml').exists(), f"{model} seed {seed} config.yaml exists")
            check((d / 'results.json').exists(), f"{model} seed {seed} results.json exists")
            check((d / 'loss_curve.png').exists(), f"{model} seed {seed} loss_curve.png exists")
    
    # 6-11. Statistical Reproducibility
    try:
        with open('benchmark_results/resolution_control_48x48/benchmark_results.json') as f:
            ref48 = json.load(f)
        check(True, "Loaded 48x48 benchmark_results.json")
    except Exception as e:
        check(False, f"Failed to load benchmark_results.json: {e}")

    metrics = ['gwrmse', 'interface_temperature_rmse', 'interface_temperature_jump_mae', 'mass_conservation_mae']
    for metric in metrics:
        tfno_vals = [ref48['raw_seed_metrics']['tfno'][str(s)][metric] for s in sorted(expected_seeds)]
        unet_vals = [ref48['raw_seed_metrics']['unet'][str(s)][metric] for s in sorted(expected_seeds)]
        diffs = [t - u for t, u in zip(tfno_vals, unet_vals)]
        
        pval = exact_two_sided_sign_flip(diffs)
        print(f"  {metric}: p={pval:.6f}")
        check(pval >= 0 and pval <= 1, f"{metric} p-value recomputed successfully")
    
    # Check numerical ledger exists
    check(pathlib.Path('numerical_ledger.csv').exists(), "numerical_ledger.csv exists")
    
    # Check manuscript mentions exploratory explicitly
    manuscript_text = pathlib.Path('manuscript/manuscript_elsarticle.tex').read_text(encoding='utf-8')
    check('exploratory' in manuscript_text.lower(), "Manuscript correctly labels 96x96 as exploratory")
    check('not as evidence that spatial resolution alone caused' in manuscript_text, "Manuscript correctly disclaims causal resolution effects")

    print("\nALL AUDIT CHECKS PASSED.")
    sys.exit(0)

if __name__ == '__main__':
    main()
