# Bounded-alpha confirmation and targeted-fix decision

Date: 2026-08-01  
Bounded-head implementation commit: `0b8f54c308170e099bcfdd4f94b5a6682cfa4e9e`  
Training and evaluation commit: `fbf5f604c2c83e889f769e3528c09e8defa9ef44`  
Decision: **NO-GO for Fix A/Fix B. The single-pair bounded-alpha reversal did not replicate as a Holm-significant multi-seed gap.**

## Executive result

T-FNO and U-Net were retrained from scratch with bounded physical-alpha output heads over the established 11 paired seeds: `42, 100, 1234, 2025, 9999, 7, 17, 314, 2718, 4242, 7777`. All 22 runs used the unchanged Phase 1 data and hyperparameters plus `--bound-alpha-output`; all ran on MPS and stopped by the declared validation-plateau rule. Each checkpoint was then evaluated on the unchanged 164-step fully autoregressive Twall-100 protocol.

The bounded T-FNO minus bounded U-Net difference in cumulative dry-area MAE was `+0.007746` (95% paired bootstrap CI `[-0.003927, +0.018293]`, exact sign-flip `p=.2230`, Holm `p=1.0`). The false-alarm-frame difference was `+22.27` (CI `[-1.91, +46.73]`, `p=.1215`, Holm `p=1.0`). Positive values favor U-Net for these error/count metrics, but both intervals include zero and neither result survives the unchanged 21-metric Holm family.

No reported metric was Holm-significant; the minimum adjusted p-value was `0.3997`. Therefore the mandated decision gate fails. Fix A (local residual convolution), Fix B (two-step pushforward training), and their combined five-seed evaluation were **not implemented or run**. Doing so after a failed gate would chase a single-seed artifact and violate the task protocol.

The final recommendation remains: **T-FNO/U-Net Pareto trade-off; retain both.**

## Part 1 methods

### Data and task

The experiment used only the three verified official 48x48 PB Subcooled tutorial trajectories already staged in `data/bubbleml/smoke_restore`: Twall-103 train, Twall-106 validation, and Twall-100 test. The model task was five past frames to five future frames for `u`, `v`, pressure gradient, temperature, and `alpha_vapor_mask=(dfun>0)`. There is one trajectory per split and no synthetic data.

The bounded head maps each alpha logit through a sigmoid between the *normalized coordinates* of physical alpha zero and one. Non-alpha outputs remain unconstrained. Audit checks confirmed alpha output indices `[4, 9, 14, 19, 24]` and `alpha_bounded=true` in every checkpoint. All 22 full rollouts were finite and every decoded alpha range remained inside `[0,1]`.

### Training protocol

All runs used 48x48 training, 24x24 effective Fourier modes, T-FNO rank 0.1, width 64, four layers, U-Net base features 32/depth 4, history/future size 5/5, batch size 8, AdamW (`lr=1e-3`, weight decay `0.01`), 3% warmup, gradient clip 1.0, horizontal reflection, minimum 20/maximum 200 epochs, and the unchanged two-window validation-plateau stop. T-FNO training consumed 1,873.8 s total (170.35 s/run mean); U-Net consumed 1,128.2 s total (102.56 s/run mean).

Artifacts:

- training histories: [`experiments/phase5_bounded_alpha_n11`](/Users/sbmahafujbondhon/dev/DD-PINNs/experiments/phase5_bounded_alpha_n11)
- checkpoints: [`checkpoints/phase5_bounded_alpha_n11`](/Users/sbmahafujbondhon/dev/DD-PINNs/checkpoints/phase5_bounded_alpha_n11)
- per-seed rollouts: [`benchmark_results/phase5_bounded_alpha_n11`](/Users/sbmahafujbondhon/dev/DD-PINNs/benchmark_results/phase5_bounded_alpha_n11)
- paired statistics: [`paired_statistics.json`](/Users/sbmahafujbondhon/dev/DD-PINNs/benchmark_results/phase5_bounded_alpha_n11/paired_statistics.json)

### Rollout and statistics

For each seed pair, frames 30--34 of Twall-100 were the only history. Each predicted five-frame bundle was fed back as the next input through source frame 198, producing 164 fully autoregressive frames. The dry-area proxy was the fraction of cells with alpha greater than 0.5 in rows 0:4. The fixed event threshold was `0.344792`, with three consecutive frames required. Ground truth never had a sustained event, so model threshold episodes are false positives and lead time is undefined.

The existing `paired_comparison` implementation was reused unchanged: 10,000 paired bootstrap resamples, exact two-sided paired sign-flip randomization, and Holm--Bonferroni correction over all 21 emitted paired metrics.

## Part 1 results

### Primary gate metrics

| Metric | T-FNO mean | U-Net mean | T-FNO - U-Net [95% bootstrap CI] | Exact p | Holm p |
|---|---:|---:|---:|---:|---:|
| cumulative dry-area MAE, 164 steps | 0.07485 | 0.06710 | +0.00775 `[-0.00393,+0.01829]` | .2230 | 1.000 |
| false-alarm frame count | 40.82 | 18.55 | +22.27 `[-1.91,+46.73]` | .1215 | 1.000 |

The initial one-pair reversal was not robust. U-Net has lower mean values for both gate metrics, but seed-to-seed variation is large enough that neither paired effect is established.

### Per-seed dry-area outcomes

| Seed | T-FNO MAE | U-Net MAE | T-FNO alarm frames | U-Net alarm frames |
|---:|---:|---:|---:|---:|
| 42 | 0.05008 | 0.08537 | 0 | 29 |
| 100 | 0.09035 | 0.05126 | 84 | 0 |
| 1234 | 0.07187 | 0.08032 | 21 | 63 |
| 2025 | 0.05917 | 0.05758 | 1 | 0 |
| 9999 | 0.12167 | 0.10382 | 146 | 98 |
| 7 | 0.05897 | 0.05275 | 8 | 0 |
| 17 | 0.07940 | 0.06834 | 27 | 9 |
| 314 | 0.06056 | 0.05319 | 3 | 0 |
| 2718 | 0.08635 | 0.06123 | 87 | 2 |
| 4242 | 0.08660 | 0.06390 | 72 | 3 |
| 7777 | 0.05828 | 0.06034 | 0 | 0 |

T-FNO has lower dry-area MAE on seeds 42, 1234, and 7777; U-Net is lower on the other eight. Alarm behavior is likewise heterogeneous. This is incompatible with treating the original n=1 ordering as a settled architectural effect.

### Standard five-field metrics at horizon 164

| Metric | T-FNO mean | U-Net mean | T-FNO - U-Net [95% bootstrap CI] | Exact p | Holm p |
|---|---:|---:|---:|---:|---:|
| RMSE | 18.3559 | 18.6562 | -0.3002 `[-0.8550,+0.2609]` | .3363 | 1.000 |
| GWRMSE | 19.4280 | 19.7887 | -0.3607 `[-0.9277,+0.2326]` | .2650 | 1.000 |
| temperature GWRMSE | 12.8114 | 13.6069 | -0.7955 `[-1.9250,+0.3207]` | .2260 | 1.000 |
| alpha GWRMSE | 0.43694 | 0.42776 | +0.00917 `[-0.01462,+0.03192]` | .4719 | 1.000 |
| interface-alpha RMSE | 0.47922 | 0.47816 | +0.00106 `[-0.04859,+0.04630]` | .9590 | 1.000 |
| interface-temperature RMSE | 15.1815 | 15.9635 | -0.7820 `[-2.6147,+1.0316]` | .4270 | 1.000 |
| interface-temperature jump MAE | 14.6450 | 14.6549 | -0.00987 `[-0.78570,+0.71392]` | .9756 | 1.000 |
| mass-conservation MAE | 0.14224 | 0.14762 | -0.00538 `[-0.02901,+0.02870]` | .7980 | 1.000 |

Cumulative mean RMSE through 164 frames favored T-FNO descriptively by `-0.06236`; its unadjusted exact p-value was `.02879`, but Holm `p=.57589`. It is therefore not a corrected significant result. Cumulative GWRMSE and mass MAE were also unresolved.

## Decision gate and Part 2

The gate required a Holm-significant U-Net bounded-alpha advantage before architectural intervention. That requirement was not met for cumulative dry-area MAE, false-alarm frames, endpoint five-field metrics, or any other member of the complete family. Accordingly:

- Fix A, the local 3x3 residual convolution branch, was not implemented.
- Fix B, two-hop autoregressive pushforward training, was not implemented.
- No combined variant was trained.
- Spectral-divergence, Sobolev, and adaptive-rank changes remain unimplemented.

This is the intended outcome of a predeclared decision gate: it prevents architecture tuning against a non-replicating single-pair observation.

## Explicit mass-conservation correction

The prior strategy text conflated two different results. The Phase 1 n=11 finding, T-FNO minus U-Net mass-conservation MAE `+0.04494` with Holm `p=.0351`, is a multi-seed held-out temporal-bundle result. The earlier bounded ablation values `0.12480` versus `0.14549` are single-seed cumulative rollout numbers at horizon 160 and point in the opposite descriptive direction. They are not the same experiment, estimator, horizon, or inferential result.

The correctly matched bounded n=11 rollout analysis now gives endpoint horizon-164 mass MAE difference `-0.00538` (Holm `p=1.0`) and cumulative mean mass MAE difference `-0.00573` (Holm `p=1.0`). Neither changes or invalidates the original Phase 1 significant conservation deficit, and neither should be labeled as that Phase 1 finding.

## Verification

Checkpoint audit: 22/22 checkpoints loaded with `weights_only=True`, declared the correct model and seed, recorded `alpha_bounded=true`, used alpha indices `[4,9,14,19,24]`, and referenced the single training commit `fbf5f604c2c83e889f769e3528c09e8defa9ef44`. SHA-256 values are recorded in every per-seed `rollout_results.json` under `provenance`.

All tracked tests pass: **21/21**. Ruff passes for the benchmark package and tracked tests, and `git diff --check` passes. A literal filesystem-wide `pytest` also discovers two unrelated untracked tests, `tests/test_geometry.py` and `tests/test_v3_architecture.py`, which fail collection because the absent `adaptive_dd_pinn.config` and `adaptive_dd_pinn.boundary_manager` modules are outside this BubbleML project. Those user-owned files were not changed or hidden.

## Final recommendation

The final architecture recommendation remains **T-FNO/U-Net Pareto trade-off; use both**. Phase 1 establishes T-FNO interface-temperature strengths and a U-Net conservation advantage under its own multi-seed protocol. The bounded 164-step study establishes physical alpha validity but does not establish a corrected long-rollout winner. Neither model is a validated CHF predictor because Twall-100 contains no sustained ground-truth event and the source has no independent heat-flux label.
