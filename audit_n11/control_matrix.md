# Control Matrix: 48x48 Tutorial vs 96x96 Resolution-Control
# (Same trajectories: Twall-103/106/100)

## Hard Control Gate Verdict: NOT_CONTROLLED

| Factor | 48x48 Tutorial Split | 96x96 Resolution-Control | Same? | Verified? |
|---|---|---|---|---|
| Spatial resolution | 48x48 | 96x96 | NO | Yes |
| Trajectories | Twall-103 (train), Twall-106 (val), Twall-100 (test) | Same: Twall-103/106/100 | YES | Yes |
| Source HDF5 checksums (48x48 originals) | Documented in CHECKSUMS.md / Sec 3.1 | NOT retained in authorized artifact set | NO | NO |
| Train/val/test trajectory roles | Documented | Same nominal roles | YES (nominal) | PARTIAL |
| Temporal frames per trajectory | 169 frames, timesteps 30-198, 160 valid windows | 166 samples; timesteps 30-195 | NO | YES |
| Rollout horizon (history/future steps) | 5 history, 5 future (cross-condition protocol) | 5 history, 5 future | YES | YES |
| Preprocessing rollout horizon for windows | 2-step validation plateau (tutorial doc) | 5-step horizon (96x96 notebook doc) | NO | PARTIAL |
| Sample count per split | 169 samples per trajectory | 166 samples per split | NO | YES |
| Model architecture | Same T-FNO, same U-Net configs | Same configs | YES | YES |
| Fourier modes | 24x24 real-FFT (48x48 Nyquist) | 24x24 real-FFT (96x96 Nyquist) | SAME COUNT, different resolution | YES |
| AdamW lr, weight decay | 1e-3, 0.01 | 1e-3, 0.01 | YES | YES (per config.yaml) |
| Batch size | 8 | 8 | YES | YES |
| Training stopping rule | 200-epoch ceiling, validation plateau | Same | YES | YES |
| Seeds | 7,17,42,100,314,1234,2025,2718,4242,7777,9999 (n=11) | Same seeds (n=11) | YES | YES |
| Optimizer | AdamW | AdamW | YES | YES |
| Loss function | MSE (data fit) | MSE (data fit) | YES | YES |
| Normalization | Field-wise normalization | Field-wise normalization | YES | YES (per scripts) |
| Evaluation metrics | Same 4 primary metrics | Same 4 primary metrics | YES | YES |
| Hardware / device | Apple M2 / MPS | Kaggle NVIDIA Tesla T4 / CUDA | NO | YES |
| Python version | 3.12.7 | Kaggle kernel (3.10+) | UNKNOWN | NO |
| PyTorch version | 2.13.0 | 2.13.0+cu130 | YES (version) / NO (build) | YES (logged) |
| Checkpoints retained | Yes (tutorial phase 1 checkpoints committed) | NO (not committed; on Kaggle only) | NO | NO |
| Source commit cross-audit | Phase 1 at commit 6dcede6 | Resolution-control at 4feb48b / 9e74e31 | NO (different revisions) | PARTIAL |
| Predeclared architecture x resolution interaction test | None declared | None declared | N/A | N/A |
| Independent statistical analysis pre-registration | No | No | N/A | N/A |

## Factors Differing

1. Spatial resolution (48x48 vs 96x96) — THE FACTOR OF INTEREST
2. Preprocessing temporal range (169 vs 166 samples; timesteps 30-198 vs 30-195)
3. Hardware (Apple M2/MPS vs NVIDIA T4/CUDA)
4. Source commits differ between experiments
5. 48x48 checkpoints retained; 96x96 checkpoints not in authorized artifact set
6. Raw source HDF5 checksums for 96x96 not independently documented

## Conclusion

Because factors 2-6 also differ, this comparison CANNOT isolate spatial
resolution as the sole varying factor.

GATE STATUS: NOT_CONTROLLED

Allowed language:
- "exploratory cross-resolution comparison"
- "stored pipeline configurations that differ in resolution and other factors"
- "descriptive differences between stored 48x48 and 96x96 configurations"

Forbidden language:
- "resolution causes the ranking reversal"
- "controlled resolution experiment"
- "architecture x resolution interaction"
- "T-FNO is better at low resolution"
- "U-Net is better at high resolution"
