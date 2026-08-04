# Multi-Trajectory Validation, Lambda Sensitivity, and Manuscript Polish

## Executive outcome

On the independent Twall-98/Twall-110 test trajectories, U-Net had the lowest mean gradient-weighted root-mean-square error (GWRMSE), interface-temperature root-mean-square error (RMSE), and interface-temperature-jump mean absolute error (MAE). The `lambda_div=.30` local-global hybrid had the lowest mass-conservation MAE. Thus T-FNO did **not** beat U-Net on this split, and the tutorial-split T-FNO-interface/U-Net-conservation trade-off did not reproduce directionally: U-Net was descriptively better on all four primary metrics than T-FNO. With only five paired seeds, however, the minimum attainable two-sided exact sign-flip p-value is .0625; no primary contrast survived Holm-Bonferroni correction. These are consistent descriptive directions, not confirmatory architecture rankings.

The expanded divergence-penalty pilot selected `lambda_div=0.30`. This is the upper tested boundary, not an estimated continuous optimum. A clean eleven-seed tutorial-split confirmation and the independent multi-trajectory test are reported below. No held-out trajectory contains a protocol-defined sustained dry-area crossing, so this cycle does not produce a CHF lead-time result.

## 1. Independent multi-trajectory validation

### Data provenance and frozen split

- Source: official Pool-Boiling Subcooled FC-72 two-dimensional legacy archive.
- Source archive SHA-256: `2eba140d74cbb7b01a55f0684227dea94306aea516a0f864831485d31d25f655`.
- Native archive: ten 384 x 384 trajectories, 201 frames each.
- Train: Twall 79, 85, 90, 95.
- Validation: Twall 81.
- Independent test: Twall 98 and 110.
- Excluded: Twall 100, 103, and 106, because they formed the earlier tutorial split.
- Training resolution: 96 x 96; continuous fields use bilinear downsampling and the binary `dfun > 0` phase mask uses nearest-neighbor downsampling.
- Temporal task: five history frames to five future frames, with physical-alpha bounds enabled for every model.

After source frames 0--29 are discarded, each included trajectory contributes 170 frame records. This yields 644 training windows, 161 validation windows, and 322 test windows. The paired seeds are 42, 100, 1234, 2025, and 9999. Training and evaluation used an actual NVIDIA Tesla T4 through CUDA.

### Primary model comparison

| Model | GWRMSE | Interface-temperature RMSE | Interface-temperature-jump MAE | Mass-conservation MAE |
|---|---:|---:|---:|---:|
| T-FNO | 11.5974 | 14.5207 | 8.7655 | 0.12989 |
| U-Net | **11.5029** | **13.9057** | **8.5757** | 0.11560 |
| Local-global hybrid | 11.6323 | 14.4567 | 8.7021 | 0.13583 |
| Divergence hybrid (`lambda_div=.30`) | 11.5859 | 14.2120 | 8.6981 | **0.08669** |

For T-FNO minus U-Net, paired differences were +0.09448 GWRMSE (95% paired seed-bootstrap interval [+0.04363,+0.14534]), +0.61497 interface-temperature RMSE ([+0.31906,+0.90941]), +0.18985 interface-temperature-jump MAE ([+0.18080,+0.19935]), and +0.01429 mass MAE ([+0.00915,+0.02085]). Each unadjusted exact two-sided sign-flip p-value was .0625 and each Holm-adjusted p-value was 1.0. The positive signs consistently favor U-Net, but exact inference at `n=5` cannot reject the paired null.

For the divergence hybrid minus U-Net, the corresponding differences were +0.08300 GWRMSE ([+0.05302,+0.10840]), +0.30630 interface-temperature RMSE ([+0.05291,+0.54161]), +0.12246 jump MAE ([+0.04257,+0.20234]), and -0.02891 mass MAE ([-0.03359,-0.02422]). The divergence hybrid therefore had the best descriptive conservation result, while U-Net retained the three accuracy/interface advantages. Relative to the zero-penalty hybrid, the penalty reduced mass MAE by 0.04913 (paired interval [-0.05283,-0.04646]); its GWRMSE and interface changes were small or favorable, but none was Holm-significant in the `n=5` family.

### Per-trajectory behavior

| Model | Test source | GWRMSE | Interface-temperature RMSE | Jump MAE | Mass MAE |
|---|---|---:|---:|---:|---:|
| T-FNO | Twall 98 | 9.4793 | 13.5316 | 8.4443 | 0.12523 |
| T-FNO | Twall 110 | 13.7155 | 15.5098 | 9.0867 | 0.13455 |
| U-Net | Twall 98 | **9.4036** | **13.0867** | **8.2500** | 0.11262 |
| U-Net | Twall 110 | **13.6023** | **14.7247** | **8.9013** | 0.11858 |
| Local-global hybrid | Twall 98 | 9.5230 | 13.4563 | 8.3684 | 0.13028 |
| Local-global hybrid | Twall 110 | 13.7415 | 15.4572 | 9.0359 | 0.14137 |
| Divergence hybrid | Twall 98 | 9.4679 | 13.2450 | 8.3650 | **0.08207** |
| Divergence hybrid | Twall 110 | 13.7039 | 15.1790 | 9.0313 | **0.09132** |

With only Twall 98 and 110 as independent tests, these contrasts expose condition heterogeneity but do not estimate population-level physical-regime uncertainty.

### Dry-area CHF proxy

The existing rule was retained: alpha above 0.5 in heater-adjacent rows 0:4, threshold `max(0.10, median(first 20 forecast frames)+0.10)`, and three consecutive threshold frames for an event.

| Held-out trajectory | Baseline | Threshold | Maximum | Frames above threshold | Longest run | Sustained event |
|---|---:|---:|---:|---:|---:|:---:|
| Twall 98 | 0.304688 | 0.404688 | 0.375000 | 0 | 0 | no |
| Twall 110 | 0.289062 | 0.389063 | 0.406250 | 1 | 1 | no |

Because neither ground truth has a sustained crossing, true-event lead time, sensitivity, and missed-event rate are undefined. The check remains a dry-area proxy analysis, not validated critical-heat-flux (CHF) detection.

### Native 384 x 384 feasibility check

| Model | Parameters | Effective modes | Epoch wall time (s) | Validation MSE | Validation divergence MAE | Validation interface-temperature RMSE |
|---|---:|---:|---:|---:|---:|---:|
| T-FNO | 548,837 | 24 x 24 | 5.91 | 1.08855 | 0.19999 | 14.3894 |
| Local-global hybrid | 696,549 | 24 x 24 | 6.09 | 0.91419 | 0.14753 | 14.6677 |
| U-Net | 7,770,169 | n/a | 2.77 | 1.27884 | 0.08986 | 17.2041 |
| Divergence hybrid (`lambda_div=.30`) | 696,549 | 24 x 24 | 6.99 | 0.91862 | 0.08771 | 14.8105 |

This balanced micro-run uses 15 frame records per selected trajectory, batch size one, seed 42, and one epoch. It tests direct-resolution execution and memory feasibility only; it cannot rank accuracy or convergence.

## 2. Divergence-penalty sensitivity

The selection pilot used the original Twall-103/Twall-106 training/validation split and never inspected Twall-100 test metrics. The zero-penalty reference and every candidate used paired seeds 42, 100, and 1234. Eligibility required both mean validation mean-squared error (MSE) and mean interface-temperature root-mean-square error (RMSE) to remain within 5% of the reference; the eligible candidate with the lowest decoded spectral-divergence mean absolute error (MAE) was selected.

Reference means were 0.453483 MSE, 0.262501 divergence MAE, and 14.5349 interface-temperature RMSE.

| `lambda_div` | Validation MSE, mean [95% seed-bootstrap interval] | Spectral-divergence MAE | Interface-temperature RMSE | Eligible |
|---:|---:|---:|---:|:---:|
| .01 | 0.453199 [0.450915, 0.454753] | 0.214625 [0.206704, 0.219187] | 14.5111 [14.4342, 14.6477] | yes |
| .03 | 0.452725 [0.450495, 0.453973] | 0.180978 [0.171951, 0.187375] | 14.6193 [14.4811, 14.8706] | yes |
| .10 | 0.451422 [0.450144, 0.452694] | 0.132893 [0.127044, 0.137126] | 14.5888 [14.4754, 14.7375] | yes |
| .20 | 0.451774 [0.450543, 0.452939] | 0.099587 [0.096092, 0.102367] | 14.4521 [14.3671, 14.5807] | yes |
| .30 | 0.450300 [0.448632, 0.451367] | 0.087281 [0.084424, 0.090052] | 14.4197 [14.3016, 14.5139] | yes |

All candidates passed both guards and divergence decreased across the tested grid, so the protocol selected 0.30. The result supports testing 0.30; it does not establish what happens above 0.30 or identify an interior optimum.

### Eleven-seed tutorial-split confirmation at 0.30

The predeclared mass-conservation non-inferiority test passed. Mean mass-conservation MAE was 0.093735 for the `lambda_div=.30` hybrid and 0.165857 for U-Net. The paired hybrid-minus-U-Net difference was -0.072122 (95% paired bootstrap interval [-0.079397, -0.065346]); the exact one-sided non-inferiority p-value was 0.000488 against the unchanged +0.008293 margin. This is the formal confirmatory claim.

Relative to the zero-penalty hybrid, mass MAE decreased by 0.110881 (paired interval [-0.115215, -0.106217]). Interface-temperature RMSE changed by +0.04127 ([-0.15731, +0.26119]) and interface-temperature-jump MAE by +0.03571 ([-0.05471, +0.10589]); neither interval establishes an interface regression. Against U-Net, the .30 model's held-out means were also descriptively lower for GWRMSE (11.0467 versus 11.1908), interface-temperature RMSE (14.9585 versus 15.5826), and interface-temperature-jump MAE (15.6407 versus 16.2070). These broader superiority contrasts were not the predeclared confirmatory target and are reported as secondary evidence.

## 3. Manuscript and artifact polish

The Methods/Results draft now includes numbered equations for the normalized-space sigmoid phase bound, the local-global hybrid layer, and the spectral divergence-penalty objective. Acronyms are expanded on first use, and the full bounded-alpha explanation is retained in Results/Discussion while the Abstract and Introduction use one-sentence references.

Core figure set generated by the reproducible plotting pipeline:

1. `figures/multitrajectory_and_polish/temperature_snapshots.png` (generated in the Colab runtime; local binary export was blocked by browser policy)
2. `figures/multitrajectory_and_polish/alpha_snapshots.png` (generated in the Colab runtime; local binary export was blocked by browser policy)
3. `figures/multitrajectory_and_polish/tutorial_twall100_dry_area_fraction_rollout.png`
4. `figures/multitrajectory_and_polish/pareto_interface_vs_conservation.png` (generated in the Colab runtime; local binary export was blocked by browser policy)
5. `figures/multitrajectory_and_polish/lambda_sensitivity_curve.png`

The Pareto error bars use one shared paired-seed bootstrap resample across models. The snapshot panels use ground truth, T-FNO, and U-Net at forecast horizons 5, 10, and 15 on held-out Twall 110.

### Computational cost

| Model | Stored parameters | Real scalar parameters | Mean training wall time/run (s) | Five-run total (s) | Inference latency (ms/window) | Throughput (windows/s) |
|---|---:|---:|---:|---:|---:|---:|
| T-FNO | 548,837 | 1,040,625 | 216.09 | 1,080.47 | 4.467 | 223.94 |
| U-Net | 7,770,169 | 7,770,169 | 98.72 | 493.62 | 2.026 | 493.63 |
| Local-global hybrid | 696,549 | 1,188,337 | 293.45 | 1,467.26 | 5.369 | 186.25 |
| Divergence hybrid | 696,549 | 1,188,337 | 294.43 | 1,472.16 | 5.384 | 185.75 |

Inference figures are synchronized model-forward timings; evaluation-loop latency, which also includes decoding and metric accumulation, remains separately available in the benchmark JSON and is not mislabeled as inference.

## 4. Verification and claim boundary

- All 20 converged 96 x 96 training runs completed under the frozen validation-plateau rule on an actual Tesla T4, and all 20 checkpoints completed paired evaluation.
- All four 384 x 384 one-epoch feasibility runs completed on the same T4 with batch size one.
- The focused benchmark/paper test suites passed 38 tests in the fully provisioned canonical environment.
- A full unfiltered local `pytest` invocation remains blocked during collection by two pre-existing, unrelated untracked tests: `tests/test_geometry.py` imports missing `adaptive_dd_pinn.config`, and `tests/test_v3_architecture.py` imports missing `adaptive_dd_pinn.boundary_manager`. They were preserved and not changed.
- Statistical audit fixes were applied before reporting: exact sign-flip enumeration no longer receives a Monte Carlo add-one correction, and compute-only metrics are excluded from the Holm family.
- The Colab artifact package was created successfully, but local export of its three cloud-rendered PNGs was blocked by browser security policy. Numerical results, local lambda/dry-area figures, and the plotting code remain reproducible; no unavailable binary is represented as locally delivered.

Five paired seeds characterize initialization uncertainty under this split. Two independent test trajectories add direct evidence about condition dependence, but they are still too few for population-level physical-regime inference. The binary phase target is derived from signed distance rather than measured continuous volume fraction; physical wall cells and independent CHF labels remain unavailable. No result here establishes experimental CHF detection, universal architecture dominance, or a continuous optimum for `lambda_div`.
