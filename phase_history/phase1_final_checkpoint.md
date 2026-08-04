# Phase 1 final checkpoint: BubbleML five-field convergence screening

Date: 2026-07-27  
Training commit: `6e71435f8ea6b988ccfa674fe6ffcecb257e2c64`  
Outcome: **NO-GO for a trustworthy paper reproduction; GO for a tested, reproducible Phase 1 screening pipeline.**

## Executive result

The iCloud failure mode is removed, the real five-field pipeline is restored, and 12 best checkpoints (four models × three seeds) now have complete configs, uninterrupted histories, real git hashes, and held-out metrics. Vanilla FNO is directionally worse than U-Net on the main interface, edge, and conservation errors. Its mean GWRMSE is 11.0634 versus 11.0379 for U-Net (paired difference +0.0255), but the three-seed paired interval crosses zero and no test survives Holm correction. This is not evidence for the paper's approximately 2× temperature-BRMSE gap.

T-FNO has the best aggregate GWRMSE (10.9923), slightly below U-Net, but remains worse than U-Net on interface-alpha RMSE, interface-temperature jump, interior-edge RMSE, and mass conservation. F-FNO is materially worse on temperature/interface errors. Therefore the factorized variants do not yet demonstrate that they close most of a reproduced U-Net gap—there is no statistically established gap here to close.

The no-go is driven by protocol and data limitations, not a failed implementation: only three official 48×48 worked-example trajectories were locally available (one trajectory per split); 64 requested Fourier modes collapse to 13 usable modes after half-resolution training; the task predicts all five fields rather than the paper's temperature target; and three U-Net/F-FNO runs were stopped by the two-minute CPU limit before the declared plateau rule.

## 1. Environment repair and data integrity

The working repository was copied with `rsync` from the iCloud-synchronized `~/Documents/DD-PINNs` tree to:

`/Users/sbmahafujbondhon/dev/DD-PINNs`

A fresh virtual environment was built there rather than copied. Runtime: Python 3.12.7, PyTorch 2.13.0, NeuralOperator 2.0.0. CUDA and MPS both reported unavailable, so every recorded run used CPU. Git was initialized before training; the restoration baseline was `7180550`, and the final training code was committed as `6e71435f8ea6b988ccfa674fe6ffcecb257e2c64`.

Full reads of every dataset key plus streaming SHA-256 completed well below one second:

| File | Size | Full-read + SHA time | SHA-256 |
|---|---:|---:|---|
| `Twall-100.hdf5` | 25 MB | 0.0272 s | `5bf2539628c3595f39517c466f6971da76f137358771592c14ad1a5881e4d1bf` |
| `Twall-103.hdf5` | 25 MB | 0.0246 s | `25b305661dee59cf5df49eb2563a4ed08f79664ba377e57877fcda5a948956dd` |
| `Twall-106.hdf5` | 25 MB | 0.0232 s | `4308e5be884c3edcf301e9c12bff8d499d53729be3820aa18e255a5152fbd004` |

No synthetic fallback was used. The preprocessor generated 507 real states: 169 each for train, validation, and test. Temporal bundling yielded 160 non-crossing windows per split. The trajectory split is:

| Split | Trajectory |
|---|---|
| train | `Twall-103.hdf5` |
| validation | `Twall-106.hdf5` |
| test | `Twall-100.hdf5` |

The restored schema is `u`, `v`, `pressure_gradient`, `temperature`, and `alpha_vapor_mask`; alpha is derived from `dfun > 0`. Split assignment is trajectory-level, and the temporal loader explicitly rejects non-consecutive timesteps and never crosses a trajectory boundary.

## 2. Restored and extended pipeline

The original five-field preprocessor, metrics, paired bootstrap, exact paired sign-flip test, and Holm–Bonferroni implementation were retained. The new temporal wrapper, model definitions, trainer, and evaluator are:

- `bubbleml_benchmark/temporal.py`
- `bubbleml_benchmark/paper_models.py`
- `bubbleml_benchmark/paper_train.py`
- `bubbleml_benchmark/paper_benchmark.py`

The end-to-end smoke passed for FNO, T-FNO, F-FNO, and U-Net: train → safe checkpoint → reload with `weights_only=True` → held-out five-field metrics. Two defects were caught and fixed during smoke testing: the unbatched half-resolution capability probe and NeuralOperator's unsafe callable/class metadata inside its custom state dictionary. Checkpoints now store tensor weights only; architecture is reconstructed from the separately validated model spec. The focused suite passes 14 tests, and Ruff passes for all new modules.

The first smoke attempt failed before an epoch because the resize probe was unbatched. A second attempt completed one FNO epoch but failed safe reload because of NeuralOperator metadata. Neither failed attempt is used as a result. The corrected one-epoch smoke and full-capacity one-epoch pilot retain their own `config.yaml`, `results.json`, checkpoints, and curves under `experiments/paper_smoke` and `experiments/paper_capacity_pilot`.

## 3. Hyperparameters and deviations

The requested settings were implemented. Values marked “deviation” prevent a paper-parity claim.

| Setting | Used | Status / justification |
|---|---|---|
| Models | vanilla FNO, Tucker FNO rank 0.1, axis-factorized F-FNO, U-Net | Requested sweep |
| Seeds | 42, 100, 1234 | **Deviation:** reduced from five to three because the environment was CPU-only |
| History / future | 5 / 5 frames | Paper-aligned framing |
| Batch size | 8 | Paper-aligned target |
| Optimizer | AdamW, LR 1e-3, weight decay 0.01 | Paper-aligned generic Table 7 setting |
| Warmup | linear, first 3% of planned optimizer steps | Implemented per step |
| LR decay | factor 0.5 every 75 epochs after warmup | Implemented; no run reached epoch 75, so it did not activate |
| Gradient clipping | global L2 norm 1.0 | Implemented and logged before clipping |
| Augmentation | one horizontal reflection per batch with probability 0.5 | Pool-boiling augmentation |
| Fourier resolution | train 24×24, validate/evaluate 48×48 | Paper-oriented half/full strategy |
| Fourier modes | requested 64×64; effective 13×13 | **Deviation:** a 24-point real FFT cannot represent 64 independent modes |
| Domain padding | zero padding, 10% on top/right, crop output | Implemented for all Fourier variants |
| FNO / T-FNO | width 64, 4 layers, instance norm, coordinate grid | Requested vanilla capacity; T-FNO Tucker rank 0.1 |
| F-FNO | width 64, 4 layers, axis-factorized spectral conv | **Deviation:** CPU-feasible implementation/capacity, not the upstream model-specific 256-wide, 7–8-layer configuration |
| U-Net | base features 32, depth 4; full-resolution train/eval | Convolutional baseline |
| Epoch budget | maximum 50; minimum 20; two-minute limit per model/seed | **Deviation:** not 250 epochs |
| Plateau rule | two consecutive checks with <0.1% relative improvement between adjacent 5-epoch validation windows | Explicit and recorded |
| Dataset | three official downsampled example trajectories | **Major deviation:** not the full BubbleML PB Subcooled training corpus |
| Prediction task | five past full states → five future full states | **Major deviation:** not the paper's temperature-only target protocol |

The paper/config comparison was checked against the [BubbleML paper](https://openreview.net/pdf?id=0Wmglu8zak), its [NeurIPS dataset page](https://papers.nips.cc/paper_files/paper/2023/hash/01726ae05d72ddba3ac784a5944fa1ef-Abstract-Datasets_and_Benchmarks.html), and the [official BubbleML repository](https://github.com/HPCForge/BubbleML). The paper's Table 7 is a generic training table; current upstream model-specific configs add architecture-dependent widths, depths, ranks, batch sizes, and maximum epochs. This report does not relabel the custom five-field task as the paper's Table 9 temperature task.

## 4. Convergence histories

![All model/seed loss curves](experiments/phase1_paper/loss_curves_all.png)

Dotted lines are training MSE and solid lines are full-resolution validation MSE. All 12 histories are uninterrupted and stored in the corresponding `results.json`.

| Model | Seed | Epochs | Best epoch | Best validation MSE | Stop | Wall time | History / curve |
|---|---:|---:|---:|---:|---|---:|---|
| FNO | 42 | 21 | 15 | 0.479182 | plateau | 100.10 s | [history](experiments/phase1_paper/fno_seed_42/results.json) / [curve](experiments/phase1_paper/fno_seed_42/loss_curve.png) |
| FNO | 100 | 21 | 14 | 0.467248 | plateau | 100.58 s | [history](experiments/phase1_paper/fno_seed_100/results.json) / [curve](experiments/phase1_paper/fno_seed_100/loss_curve.png) |
| FNO | 1234 | 23 | 10 | 0.470068 | plateau | 109.50 s | [history](experiments/phase1_paper/fno_seed_1234/results.json) / [curve](experiments/phase1_paper/fno_seed_1234/loss_curve.png) |
| T-FNO | 42 | 24 | 18 | 0.461947 | plateau | 121.21 s | [history](experiments/phase1_paper/tfno_seed_42/results.json) / [curve](experiments/phase1_paper/tfno_seed_42/loss_curve.png) |
| T-FNO | 100 | 23 | 18 | 0.460313 | plateau | 124.07 s | [history](experiments/phase1_paper/tfno_seed_100/results.json) / [curve](experiments/phase1_paper/tfno_seed_100/loss_curve.png) |
| T-FNO | 1234 | 21 | 21 | 0.466587 | plateau | 109.38 s | [history](experiments/phase1_paper/tfno_seed_1234/results.json) / [curve](experiments/phase1_paper/tfno_seed_1234/loss_curve.png) |
| F-FNO | 42 | 21 | 13 | 0.475349 | plateau | 114.91 s | [history](experiments/phase1_paper/ffno_seed_42/results.json) / [curve](experiments/phase1_paper/ffno_seed_42/loss_curve.png) |
| F-FNO | 100 | 21 | 14 | 0.476309 | plateau | 114.77 s | [history](experiments/phase1_paper/ffno_seed_100/results.json) / [curve](experiments/phase1_paper/ffno_seed_100/loss_curve.png) |
| F-FNO | 1234 | 22 | 18 | 0.472252 | time limit before plateau | 120.04 s | [history](experiments/phase1_paper/ffno_seed_1234/results.json) / [curve](experiments/phase1_paper/ffno_seed_1234/loss_curve.png) |
| U-Net | 42 | 24 | 20 | 0.452386 | plateau | 103.25 s | [history](experiments/phase1_paper/unet_seed_42/results.json) / [curve](experiments/phase1_paper/unet_seed_42/loss_curve.png) |
| U-Net | 100 | 29 | 27 | 0.450773 | time limit before plateau | 123.68 s | [history](experiments/phase1_paper/unet_seed_100/results.json) / [curve](experiments/phase1_paper/unet_seed_100/loss_curve.png) |
| U-Net | 1234 | 29 | 29 | 0.444168 | time limit before plateau | 124.02 s | [history](experiments/phase1_paper/unet_seed_1234/results.json) / [curve](experiments/phase1_paper/unet_seed_1234/loss_curve.png) |

The training/validation separation grows for every model, which is consistent with overfitting one training trajectory. “Plateau” here means only the declared local moving-window rule, not publication-grade convergence.

## 5. Held-out five-field benchmark

Values below are the across-seed mean ± the existing 95% normal half-width (`1.96 × sample SD / sqrt(3)`). Lower is better for every error metric. The evaluator averages all five frames in the first future bundle over 160 held-out windows. Because `rollout_bundles=1`, every emitted `rollout_*` field is numerically identical to its one-bundle counterpart and is not duplicated in this table; it remains present in the raw JSON and CSV.

| Metric | FNO | T-FNO | F-FNO | U-Net |
|---|---:|---:|---:|---:|
| relative L2 | 0.87764 ± 0.0116 | 0.87115 ± 0.00475 | 0.85411 ± 0.00368 | **0.85257 ± 0.0120** |
| RMSE | 9.24753 ± 0.0287 | 9.18317 ± 0.0317 | 9.30761 ± 0.139 | **9.15951 ± 0.0394** |
| GWRMSE | 11.06340 ± 0.0243 | **10.99231 ± 0.0159** | 11.16642 ± 0.119 | 11.03786 ± 0.0297 |
| temperature GWRMSE | 11.96928 ± 0.0835 | **11.92034 ± 0.0450** | 12.23866 ± 0.0857 | 11.92685 ± 0.110 |
| alpha GWRMSE | 0.39257 ± 0.00822 | 0.39111 ± 0.00804 | **0.38514 ± 0.00361** | 0.38673 ± 0.000855 |
| interface alpha RMSE | 0.46930 ± 0.00360 | 0.46650 ± 0.00453 | 0.46784 ± 0.000573 | **0.45436 ± 0.00641** |
| interface temperature RMSE | 15.08438 ± 0.0226 | 14.96650 ± 0.184 | 15.74457 ± 0.0716 | **14.77324 ± 0.133** |
| interface temperature-jump MAE | 16.22882 ± 0.144 | 16.49175 ± 0.160 | 17.38232 ± 0.101 | **16.05686 ± 0.0776** |
| interior-edge RMSE | 10.26969 ± 0.0543 | 10.24721 ± 0.0786 | 10.48487 ± 0.102 | **10.07395 ± 0.0176** |
| interior-edge divergence MAE | 0.25302 ± 0.0198 | **0.22855 ± 0.00985** | 0.25382 ± 0.0211 | 0.24284 ± 0.0244 |
| mass-conservation MAE | 0.23025 ± 0.0129 | 0.19672 ± 0.00275 | 0.21756 ± 0.00782 | **0.16218 ± 0.00822** |
| latency, ms/window (CPU) | 20.816 ± 0.407 | 21.783 ± 0.371 | 24.537 ± 0.161 | **11.683 ± 0.255** |
| throughput, windows/s (CPU) | 48.05 ± 0.93 | 45.91 ± 0.79 | 40.76 ± 0.27 | **85.62 ± 1.85** |
| PyTorch parameters | 1,547,993 | 212,645 | 506,137 | 7,770,169 |
| real-scalar parameters | 3,038,937 | 368,241 | 932,121 | 7,770,169 |

The combined RMSE/GWRMSE mixes fields with different units and scales and should be interpreted only within this exact fixed protocol. The example files omit physical wall cells and coordinate grids. Consequently `interior_edge_*` measures outer released grid cells, not a physical wall residual, and divergence uses grid-cell spacing 1.0.

Complete machine-readable results: [benchmark JSON](benchmark_results/phase1_paper/benchmark_results.json) and [long-form CSV](benchmark_results/phase1_paper/benchmark_summary.csv).

## 6. Paired statistics versus U-Net

Each entry is model-minus-U-Net paired mean difference `[95% paired bootstrap interval]`; positive means higher error (worse). The final number is the unchanged exact paired sign-flip p-value. There are only three paired seeds. Every Holm–Bonferroni adjusted p-value across the full emitted metric family is 1.0.

| Error metric | FNO − U-Net | T-FNO − U-Net | F-FNO − U-Net |
|---|---:|---:|---:|
| relative L2 | +0.02507 `[+0.00590,+0.04305]`; p=.333 | +0.01858 `[+0.00504,+0.02946]`; p=.333 | +0.00154 `[-0.01439,+0.01032]`; p=1.000 |
| RMSE | +0.08802 `[+0.04924,+0.13257]`; p=.333 | +0.02366 `[+0.01294,+0.04036]`; p=.333 | +0.14810 `[+0.06100,+0.24250]`; p=.333 |
| GWRMSE | +0.02554 `[-0.02207,+0.05968]`; p=.556 | −0.04555 `[−0.05439,−0.02872]`; p=.333 | +0.12856 `[+0.07687,+0.22547]`; p=.333 |
| temperature GWRMSE | +0.04243 `[-0.00970,+0.12367]`; p=.556 | −0.00651 `[−0.15082,+0.12040]`; p=1.000 | +0.31182 `[+0.15387,+0.48497]`; p=.333 |
| alpha GWRMSE | +0.00584 `[+0.00097,+0.01510]`; p=.333 | +0.00438 `[−0.00114,+0.01210]`; p=.556 | −0.00158 `[−0.00552,+0.00208]`; p=.778 |
| interface alpha RMSE | +0.01494 `[+0.00697,+0.02426]`; p=.333 | +0.01215 `[+0.00927,+0.01610]`; p=.333 | +0.01349 `[+0.00739,+0.01909]`; p=.333 |
| interface temperature RMSE | +0.31114 `[+0.19324,+0.46216]`; p=.333 | +0.19326 `[−0.02058,+0.41130]`; p=.556 | +0.97133 `[+0.83637,+1.17262]`; p=.333 |
| interface temperature-jump MAE | +0.17196 `[+0.01801,+0.36836]`; p=.333 | +0.43489 `[+0.19437,+0.55844]`; p=.333 | +1.32546 `[+1.16504,+1.44880]`; p=.333 |
| interior-edge RMSE | +0.19575 `[+0.14284,+0.24839]`; p=.333 | +0.17326 `[+0.10244,+0.26712]`; p=.333 | +0.41092 `[+0.34598,+0.53016]`; p=.333 |
| interior-edge divergence MAE | +0.01018 `[−0.00389,+0.03142]`; p=.778 | −0.01429 `[−0.03200,+0.00122]`; p=.556 | +0.01098 `[−0.02818,+0.04506]`; p=.778 |
| mass-conservation MAE | +0.06807 `[+0.05601,+0.08346]`; p=.333 | +0.03454 `[+0.02410,+0.04288]`; p=.333 | +0.05538 `[+0.04344,+0.06417]`; p=.333 |

Intervals that exclude zero with n=3 are descriptive bootstrap intervals, not sufficient evidence after multiplicity correction. The exact sign-flip test has very coarse resolution at three pairs.

## 7. Decision and next required run

**NO-GO: this is not yet a trustworthy paper-aligned baseline and must not be presented as a reproduction of Table 9.** It is a credible engineering checkpoint: real data only, leakage-safe temporal framing, four working models, safe checkpoints, full histories, best-weight evaluation, and unchanged multi-seed statistics.

The next decisive run needs the full official PB Subcooled corpus and paper temperature-target construction, a grid/resolution where 64 modes are actually representable, five seeds, model-specific upstream capacities, and enough GPU time for all models—including U-Net—to plateau. Until then:

1. Treat the observed vanilla-FNO disadvantage on interface/edge/conservation metrics as a hypothesis-generating signal, not a confirmed scientific gap.
2. Treat T-FNO's lower aggregate GWRMSE as promising but mixed: it does not beat U-Net on interface continuity or mass conservation.
3. Do not infer a Gibbs-ringing mechanism from aggregate metrics alone; field/spectrum diagnostics on the full-resolution task are still required.

