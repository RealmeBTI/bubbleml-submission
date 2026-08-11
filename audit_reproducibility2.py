import json
import numpy as np
from scipy import stats

def calculate_stats(data):
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    # 95% CI using t-distribution
    ci = stats.t.ppf(0.975, n-1) * (std / np.sqrt(n))
    return mean, std, ci, n

def main():
    with open("benchmark_results/resolution_control_48x48/benchmark_results.json") as f:
        bench_data = json.load(f)
    
    raw = bench_data["raw_seed_metrics"]
    metrics = ["gwrmse", "interface_temperature_rmse", "interface_temperature_jump_mae", "mass_conservation_mae"]
    
    tfno_data = {m: [] for m in metrics}
    unet_data = {m: [] for m in metrics}
    
    seeds = ["42", "100", "1234", "2025", "9999", "7", "17", "314", "2718", "4242", "7777"]
    
    for seed in seeds:
        for m in metrics:
            tfno_data[m].append(raw["tfno"][seed][m])
            unet_data[m].append(raw["unet"][seed][m])
            
    # Output individual stats
    print("=== TFNO ===")
    for m in metrics:
        mean, std, ci, n = calculate_stats(tfno_data[m])
        print(f"{m}:\n  mean = {mean}\n  std  = {std}\n  CI95 = {ci}\n  n    = {n}")
        
    print("\n=== UNET ===")
    for m in metrics:
        mean, std, ci, n = calculate_stats(unet_data[m])
        print(f"{m}:\n  mean = {mean}\n  std  = {std}\n  CI95 = {ci}\n  n    = {n}")

    # Paired stats
    print("\n=== PAIRED STATS (TFNO - UNET) ===")
    for m in metrics:
        diffs = np.array(tfno_data[m]) - np.array(unet_data[m])
        mean_diff = np.mean(diffs)
        n = len(diffs)
        std_diff = np.std(diffs, ddof=1)
        ci_val = stats.t.ppf(0.975, n-1) * (std_diff / np.sqrt(n))
        ci_lower = mean_diff - ci_val
        ci_upper = mean_diff + ci_val
        
        # Exact sign-flip test
        test_stat = np.sum(diffs)
        count_extreme = 0
        total_perms = 2**n
        for i in range(total_perms):
            signs = np.array([1 if (i & (1 << j)) else -1 for j in range(n)])
            perm_stat = np.sum(diffs * signs)
            if abs(perm_stat) >= abs(test_stat):
                count_extreme += 1
        p_val = count_extreme / total_perms
        
        print(f"{m}:\n  mean = {mean_diff:+.4e}\n  CI = [{ci_lower}, {ci_upper}]\n  p = {p_val}")

if __name__ == "__main__":
    main()
