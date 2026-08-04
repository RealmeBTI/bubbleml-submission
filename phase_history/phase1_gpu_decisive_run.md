# Phase 1 GPU decisive run: five-field BubbleML benchmark

## Decision

**No model is a statistically defensible overall replacement for U-Net on this benchmark.** T-FNO remains the leading operator candidate, but the converged result is a Pareto tradeoff rather than a clean win:

- T-FNO's mean GWRMSE is lower than U-Net's by `0.05698`, but the paired result is not significant (`95% bootstrap CI [-0.12314, 0.00946]`, sign-flip `p=.1469`, Holm `p=1.0`, `n=11`).
- T-FNO is significantly better on interface-temperature RMSE (`Δ=-0.50190`, Holm `p=.0488`) and interface-temperature jump MAE (`Δ=-0.43147`, Holm `p=.0351`).
- T-FNO is significantly worse on mass-conservation MAE (`Δ=+0.04494`, Holm `p=.0351`).

Therefore:

1. **Do not declare T-FNO, FNO, or F-FNO an overall improvement over U-Net.**
2. **Do not start CHF rollout with a single “winning” architecture.** If CHF work begins now, carry T-FNO and U-Net together as a two-model Pareto comparison: T-FNO for interface-temperature fidelity and U-Net as the conservation/general-error control.
3. The single targeted fix before making a benchmark-wide architecture claim is **more independent training trajectories**, staged on external or cluster storage. More epochs are not the missing ingredient: every run reached the declared plateau rule well below the 200-epoch ceiling.

This is this project's custom five-field temporal-bundle protocol—temperature, `u`, `v`, pressure gradient, and vapor mask—not a reproduction of BubbleML Table 9.

## Reproducibility identity

| Item | Recorded value |
|---|---|
| Canonical repository | `/Users/sbmahafujbondhon/dev/DD-PINNs` |
| Training-code commit | `6dcede6e1f0495c0a298ff7c34cba3f71e4b583f` (`Train Fourier baselines at valid full-grid modes`) |
| Main experiment | [`experiments/phase1_gpu_decisive`](experiments/phase1_gpu_decisive) |
| Main four-model benchmark (`n=5`) | [`benchmark_results/phase1_gpu_decisive/benchmark_results.json`](benchmark_results/phase1_gpu_decisive/benchmark_results.json) / [CSV](benchmark_results/phase1_gpu_decisive/benchmark_summary.csv) |
| T-FNO/U-Net extension (`n=11`) | [`benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_results.json`](benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_results.json) / [CSV](benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_summary.csv) |
| Checkpoints | [`checkpoints/phase1_gpu_decisive`](checkpoints/phase1_gpu_decisive) |
| Main loss figure | [`loss_curves_main_n5.png`](experiments/phase1_gpu_decisive/loss_curves_main_n5.png) |
| T-FNO/U-Net extension figure | [`loss_curves_tfno_unet_n11.png`](experiments/phase1_gpu_decisive/loss_curves_tfno_unet_n11.png) |

All benchmark JSON files record exactly one checkpoint commit: `6dcede6e1f0495c0a298ff7c34cba3f71e4b583f`.

## GPU confirmation and smoke test

The runtime was macOS 26.5 on an Apple M2 with a 10-core integrated GPU, Python 3.12.7, and PyTorch 2.13.0. CUDA was unavailable; `torch.backends.mps.is_built()` and `torch.backends.mps.is_available()` both returned `True`, so the GPU backend was **MPS**.

Before the mode correction, the existing unchanged one-epoch test completed for all four models at commit `95e3ec7` under [`experiments/gpu_smoke_pre_fix`](experiments/gpu_smoke_pre_fix):

| Model | Device | Epoch wall time | Status |
|---|---:|---:|---|
| FNO | MPS | 6.07 s | completed |
| T-FNO | MPS | 4.19 s | completed |
| F-FNO | MPS | 6.50 s | completed |
| U-Net | MPS | 4.45 s | completed |

A three-epoch, full-capacity post-fix pilot under [`experiments/gpu_capacity_pilot`](experiments/gpu_capacity_pilot) confirmed 48×48 training and effective 24×24 modes. Mean sustained epoch times after the compilation-heavy first epoch were FNO 6.33 s, T-FNO 6.49 s, F-FNO 7.37 s, and U-Net 2.73 s.

The earlier report's “100–124 s CPU” values were **whole-run wall times**, not per-epoch times. From those histories, typical CPU epochs at half resolution were approximately 4.7 s (FNO), 5.4 s (T-FNO/F-FNO), and 4.2 s (U-Net). MPS accelerates full-capacity U-Net substantially, while the complex FFT models are slightly slower per epoch because this run performs the larger full-resolution Fourier workload. The useful gain is that MPS makes uncapped U-Net convergence cheap and keeps every model within a few seconds per epoch.

## Fourier ceiling correction

The Fourier family now trains on the native **48×48** grid (`fourier_downsample_factor=1`). For a real FFT with length `N=48`, the non-redundant last-axis spectrum contains

```text
N / 2 + 1 = 48 / 2 + 1 = 25 bins.
```

The configuration deliberately uses **24×24 modes**, just below that 25-bin ceiling. This replaces the invalid request for 64 modes and removes the previous half-resolution collapse to 13 effective modes. Every Fourier checkpoint records requested and effective modes as `[24, 24]`; every run config records native and training resolution as `[48, 48]`. This is a grid/Nyquist correction, not a capacity-tuning choice.

No 64-mode native-resolution experiment was attempted: the higher-resolution corpus could not be staged, and the task explicitly made trajectory expansion the prerequisite for that experiment.

## Data and scope decision

The benchmark used the three real, official downsampled PB Subcooled tutorial trajectories already verified locally. The official BubbleML site describes these examples as a small downsampled subset and directs full-study downloads through its data documentation. BubbleML 2.0's official Hugging Face dataset provides explicit train/test splits; its FC-72 PB Subcooled directory is 336 GB and lists individual trajectories at about 16.8 GB each. See the [BubbleML project](https://hpcforge.github.io/BubbleML/), [BubbleML 2.0 dataset card](https://huggingface.co/datasets/hpcforge/BubbleML_2), and [FC-72 PB Subcooled files](https://huggingface.co/datasets/hpcforge/BubbleML_2/tree/main/PoolBoiling-Subcooled-FC72-2D).

The older official PB Subcooled archive was probed at `11,108,940,120` bytes (about 10.35 GiB), with HTTP range support, but the machine had only about 6.5 GiB free and observed transfer was roughly 40 KB/s. BubbleML 2.0 was still larger: a probed HDF5 trajectory was `16,785,618,952` bytes. Downloading either source would exceed local free space. The probe was stopped without leaving a partial dataset.

Consequently, the explicit scope is:

| Split | Source | Frames | Temporal windows (history 5 / future 5) |
|---|---|---:|---:|
| train | `Twall-103.hdf5` | 169 | 160 |
| validation | `Twall-106.hdf5` | 169 | 160 |
| test | `Twall-100.hdf5` | 169 | 160 |

Trajectory boundaries remain intact: one complete trajectory belongs to each split, with no cross-trajectory windows. This preserves split correctness but does **not** solve the single-training-trajectory overfitting limitation.

### Source checksums

| File | SHA-256 |
|---|---|
| `Twall-100.hdf5` | `5bf2539628c3595f39517c466f6971da76f137358771592c14ad1a5881e4d1bf` |
| `Twall-103.hdf5` | `25b305661dee59cf5df49eb2563a4ed08f79664ba377e57877fcda5a948956dd` |
| `Twall-106.hdf5` | `4308e5be884c3edcf301e9c12bff8d499d53729be3820aa18e255a5152fbd004` |

## Convergence protocol

| Setting | Value |
|---|---|
| Main seeds, all four models | `42, 100, 1234, 2025, 9999` |
| Confirmatory extension | T-FNO and U-Net only: `7, 17, 314, 2718, 4242, 7777` |
| Epoch limits | minimum 20, maximum 200, no wall-clock cap |
| Stop rule | two consecutive adjacent 5-epoch windows with less than 0.1% relative validation improvement |
| Optimizer | AdamW, LR `1e-3`, weight decay `0.01` |
| Schedule | 3% linear warmup; factor `0.5` step decay after 75 epochs |
| Gradient clip | `1.0` |
| Batch / workers | `8` / `0` |
| Temporal bundle | history 5 / future 5, five fields each (`25→25` channels) |
| Augmentation | horizontal reflection enabled |
| FNO / T-FNO | width 64, 4 layers, domain padding 0.1; T-FNO rank 0.1 |
| F-FNO | width 64, 4 layers |
| U-Net | base features 32, depth 4 |
| Fourier grid / modes | 48×48 / requested and effective 24×24 |
| Evaluation | batch 8, one rollout bundle, 10,000 bootstrap samples, MPS |

The five-seed main comparison was run first exactly as requested. With `n=5`, the exact two-sided paired sign-flip test with the implementation's add-one correction cannot return less than `3/33=.0909`, even before Holm correction. The main comparison therefore cannot establish `p<.05` by construction. After observing that limitation, six fixed additional seeds were run for the pre-identified leading comparison, T-FNO versus U-Net. This `n=11` extension is fully disclosed and should be treated as confirmatory evidence for that pair, not as a pre-registered four-model experiment.

## Full loss histories and stopping

All 32 runs completed on MPS, reached `validation_plateau`, and stopped before the 200-epoch ceiling. Each linked `results.json` contains every epoch's training MSE, validation MSE, learning rate, gradient norm, wall time, and plateau statistic; the adjacent PNG is that run's curve.

### Main four-model, five-seed run

| Model | Seed | Epochs | Best epoch | Best validation MSE | Wall time | History / curve |
|---|---:|---:|---:|---:|---:|---|
| FNO | 42 | 21 | 11 | 0.469741 | 132.75 s | [history](experiments/phase1_gpu_decisive/fno_seed_42/results.json) / [curve](experiments/phase1_gpu_decisive/fno_seed_42/loss_curve.png) |
| FNO | 100 | 21 | 12 | 0.469456 | 132.77 s | [history](experiments/phase1_gpu_decisive/fno_seed_100/results.json) / [curve](experiments/phase1_gpu_decisive/fno_seed_100/loss_curve.png) |
| FNO | 1234 | 21 | 11 | 0.472775 | 137.57 s | [history](experiments/phase1_gpu_decisive/fno_seed_1234/results.json) / [curve](experiments/phase1_gpu_decisive/fno_seed_1234/loss_curve.png) |
| FNO | 2025 | 21 | 12 | 0.471919 | 167.54 s | [history](experiments/phase1_gpu_decisive/fno_seed_2025/results.json) / [curve](experiments/phase1_gpu_decisive/fno_seed_2025/loss_curve.png) |
| FNO | 9999 | 21 | 12 | 0.471575 | 136.97 s | [history](experiments/phase1_gpu_decisive/fno_seed_9999/results.json) / [curve](experiments/phase1_gpu_decisive/fno_seed_9999/loss_curve.png) |
| T-FNO | 42 | 24 | 22 | 0.454198 | 150.20 s | [history](experiments/phase1_gpu_decisive/tfno_seed_42/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_42/loss_curve.png) |
| T-FNO | 100 | 27 | 17 | 0.460767 | 167.84 s | [history](experiments/phase1_gpu_decisive/tfno_seed_100/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_100/loss_curve.png) |
| T-FNO | 1234 | 23 | 17 | 0.462421 | 143.53 s | [history](experiments/phase1_gpu_decisive/tfno_seed_1234/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_1234/loss_curve.png) |
| T-FNO | 2025 | 25 | 19 | 0.458247 | 151.70 s | [history](experiments/phase1_gpu_decisive/tfno_seed_2025/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_2025/loss_curve.png) |
| T-FNO | 9999 | 27 | 21 | 0.451594 | 163.45 s | [history](experiments/phase1_gpu_decisive/tfno_seed_9999/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_9999/loss_curve.png) |
| F-FNO | 42 | 21 | 14 | 0.464110 | 140.72 s | [history](experiments/phase1_gpu_decisive/ffno_seed_42/results.json) / [curve](experiments/phase1_gpu_decisive/ffno_seed_42/loss_curve.png) |
| F-FNO | 100 | 21 | 14 | 0.462804 | 132.46 s | [history](experiments/phase1_gpu_decisive/ffno_seed_100/results.json) / [curve](experiments/phase1_gpu_decisive/ffno_seed_100/loss_curve.png) |
| F-FNO | 1234 | 21 | 15 | 0.464633 | 149.35 s | [history](experiments/phase1_gpu_decisive/ffno_seed_1234/results.json) / [curve](experiments/phase1_gpu_decisive/ffno_seed_1234/loss_curve.png) |
| F-FNO | 2025 | 21 | 11 | 0.464527 | 147.73 s | [history](experiments/phase1_gpu_decisive/ffno_seed_2025/results.json) / [curve](experiments/phase1_gpu_decisive/ffno_seed_2025/loss_curve.png) |
| F-FNO | 9999 | 21 | 14 | 0.463812 | 148.04 s | [history](experiments/phase1_gpu_decisive/ffno_seed_9999/results.json) / [curve](experiments/phase1_gpu_decisive/ffno_seed_9999/loss_curve.png) |
| U-Net | 42 | 33 | 27 | 0.442621 | 90.09 s | [history](experiments/phase1_gpu_decisive/unet_seed_42/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_42/loss_curve.png) |
| U-Net | 100 | 23 | 20 | 0.452534 | 63.06 s | [history](experiments/phase1_gpu_decisive/unet_seed_100/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_100/loss_curve.png) |
| U-Net | 1234 | 33 | 27 | 0.443268 | 89.61 s | [history](experiments/phase1_gpu_decisive/unet_seed_1234/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_1234/loss_curve.png) |
| U-Net | 2025 | 27 | 23 | 0.450768 | 73.90 s | [history](experiments/phase1_gpu_decisive/unet_seed_2025/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_2025/loss_curve.png) |
| U-Net | 9999 | 33 | 23 | 0.446318 | 89.75 s | [history](experiments/phase1_gpu_decisive/unet_seed_9999/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_9999/loss_curve.png) |

### Six-seed T-FNO/U-Net extension

| Model | Seed | Epochs | Best epoch | Best validation MSE | Wall time | History / curve |
|---|---:|---:|---:|---:|---:|---|
| T-FNO | 7 | 29 | 17 | 0.458674 | 223.19 s | [history](experiments/phase1_gpu_decisive/tfno_seed_7/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_7/loss_curve.png) |
| T-FNO | 17 | 25 | 19 | 0.459708 | 178.76 s | [history](experiments/phase1_gpu_decisive/tfno_seed_17/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_17/loss_curve.png) |
| T-FNO | 314 | 26 | 20 | 0.462177 | 202.46 s | [history](experiments/phase1_gpu_decisive/tfno_seed_314/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_314/loss_curve.png) |
| T-FNO | 2718 | 25 | 20 | 0.458203 | 206.73 s | [history](experiments/phase1_gpu_decisive/tfno_seed_2718/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_2718/loss_curve.png) |
| T-FNO | 4242 | 23 | 22 | 0.462519 | 145.42 s | [history](experiments/phase1_gpu_decisive/tfno_seed_4242/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_4242/loss_curve.png) |
| T-FNO | 7777 | 27 | 18 | 0.461286 | 172.34 s | [history](experiments/phase1_gpu_decisive/tfno_seed_7777/results.json) / [curve](experiments/phase1_gpu_decisive/tfno_seed_7777/loss_curve.png) |
| U-Net | 7 | 33 | 28 | 0.439600 | 92.29 s | [history](experiments/phase1_gpu_decisive/unet_seed_7/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_7/loss_curve.png) |
| U-Net | 17 | 36 | 36 | 0.446256 | 100.66 s | [history](experiments/phase1_gpu_decisive/unet_seed_17/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_17/loss_curve.png) |
| U-Net | 314 | 30 | 24 | 0.446298 | 84.20 s | [history](experiments/phase1_gpu_decisive/unet_seed_314/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_314/loss_curve.png) |
| U-Net | 2718 | 35 | 29 | 0.444162 | 97.98 s | [history](experiments/phase1_gpu_decisive/unet_seed_2718/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_2718/loss_curve.png) |
| U-Net | 4242 | 28 | 25 | 0.444395 | 80.08 s | [history](experiments/phase1_gpu_decisive/unet_seed_4242/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_4242/loss_curve.png) |
| U-Net | 7777 | 36 | 31 | 0.447829 | 101.37 s | [history](experiments/phase1_gpu_decisive/unet_seed_7777/results.json) / [curve](experiments/phase1_gpu_decisive/unet_seed_7777/loss_curve.png) |

The loss curves retain the previous single-trajectory signature: training loss continues downward after validation flattens. The plateau rule prevents further fitting to that gap.

## Main four-model held-out metrics (`n=5`)

Lower is better for all error metrics; throughput is the exception. Values below are seed means. Confidence intervals and raw per-seed values are in the linked JSON/CSV.

| Metric | FNO | T-FNO | F-FNO | U-Net |
|---|---:|---:|---:|---:|
| relative L2 | 0.877158 | 0.869104 | **0.862648** | 0.868703 |
| RMSE | 9.194703 | 9.226062 | 9.198083 | **9.172008** |
| GWRMSE | 11.146334 | **11.108273** | 11.145171 | 11.159977 |
| temperature GWRMSE | 12.387729 | **12.141343** | 12.424827 | 12.473187 |
| alpha GWRMSE | 0.395773 | 0.393670 | **0.391499** | 0.392731 |
| interface alpha RMSE | 0.464162 | **0.464068** | 0.464784 | 0.464817 |
| interface temperature RMSE | 15.166165 | **15.004756** | 15.194814 | 15.517546 |
| interface temperature jump MAE | 15.962678 | **15.766023** | 16.231071 | 16.132977 |
| interior-edge RMSE | 10.242768 | 10.251598 | 10.227925 | **10.211802** |
| interior-edge divergence MAE | 0.280836 | **0.231371** | 0.258300 | 0.232723 |
| mass-conservation MAE | 0.259338 | 0.213149 | 0.225510 | **0.160183** |
| real scalar parameters | 10,280,665 | **1,040,625** | 1,653,017 | 7,770,169 |
| latency, ms/window (MPS) | 49.90 | 49.89 | 52.20 | **43.39** |
| throughput, windows/s (MPS) | 20.05 | 20.05 | 19.16 | **23.05** |

At five seeds, T-FNO's GWRMSE difference from U-Net was `-0.05170` (`p=.2121`, Holm `p=1.0`). FNO and F-FNO differed by `-0.01364` and `-0.01481`; both Holm values were `1.0`. Thus none of the four-model differences was statistically resolved in the main comparison.

## T-FNO versus U-Net (`n=11`)

`Δ` is paired T-FNO minus U-Net, so negative error deltas favor T-FNO. The Holm correction is the existing benchmark implementation unchanged; it corrects the full recorded comparison family, including matching rollout aliases and performance metrics, and is therefore conservative. With one rollout bundle, rollout aliases equal the corresponding one-bundle metrics and are omitted from this display but retained in the JSON.

| Metric | T-FNO mean ± 95% CI half-width | U-Net mean ± 95% CI half-width | Paired Δ [95% bootstrap CI] | Sign-flip p | Holm p | Result |
|---|---:|---:|---:|---:|---:|---|
| relative L2 | 0.871031 ± 0.002835 | 0.865389 ± 0.005400 | +0.005642 [+0.000726,+0.010760] | .0639 | .6618 | unresolved |
| RMSE | 9.235539 ± 0.030558 | 9.187373 ± 0.031200 | +0.048166 [+0.007580,+0.090682] | .0551 | .6618 | unresolved |
| GWRMSE | 11.133855 ± 0.052873 | 11.190835 ± 0.047100 | -0.056980 [-0.123140,+0.009464] | .1469 | 1.0 | unresolved |
| temperature GWRMSE | 12.218303 ± 0.164533 | 12.527914 ± 0.162000 | -0.309611 [-0.546191,-0.081319] | .0356 | .4988 | unresolved after Holm |
| alpha GWRMSE | 0.394150 ± 0.004277 | 0.396487 ± 0.003740 | -0.002337 [-0.007730,+0.003246] | .4485 | 1.0 | unresolved |
| interface alpha RMSE | 0.465298 ± 0.001947 | 0.467708 ± 0.003450 | -0.002410 [-0.005791,+0.001204] | .2191 | 1.0 | unresolved |
| interface temperature RMSE | 15.080698 ± 0.142366 | 15.582596 ± 0.184000 | -0.501897 [-0.740654,-0.283009] | .00244 | **.0488** | **T-FNO better** |
| interface temperature jump MAE | 15.775556 ± 0.070312 | 16.207022 ± 0.077900 | -0.431466 [-0.539541,-0.340299] | .00146 | **.0351** | **T-FNO better** |
| interior-edge RMSE | 10.271010 ± 0.063429 | 10.207558 ± 0.023900 | +0.063452 [+0.016821,+0.125105] | .0142 | .2406 | unresolved after Holm |
| interior-edge divergence MAE | 0.231325 ± 0.005858 | 0.239470 ± 0.009750 | -0.008144 [-0.018531,+0.002011] | .1674 | 1.0 | unresolved |
| mass-conservation MAE | 0.210793 ± 0.002952 | 0.165857 ± 0.005560 | +0.044936 [+0.038529,+0.051223] | .00146 | **.0351** | **T-FNO worse** |

The prior mixed picture persists and is now sharper: T-FNO's interface-temperature advantage is real under the unchanged multiple-testing procedure, but so is its conservation deficit. Its overall GWRMSE lead does not survive paired inference.

## Deviations and limitations

| Requested or ideal condition | Actual run | Consequence |
|---|---|---|
| CUDA or supported Apple GPU | Apple M2 MPS, honestly detected and recorded | Valid GPU execution; Fourier FFT throughput is not CUDA-like |
| Expand to 5–10 training trajectories | 1 train / 1 validation / 1 test trajectory | **Major limitation:** generalization and overfitting cannot be resolved |
| All four models across five seeds | Completed exactly | Main comparison satisfied |
| Statistical power for T-FNO/U-Net | Added six paired seeds after the `n=5` exact-test floor was identified | `n=11` resolves interface/conservation effects; extension was not pre-registered |
| 48×48 Fourier training at 24 modes | Completed exactly | Previous 13-mode collapse removed |
| 64 modes at higher native resolution if data/time remained | Not run because expanded data could not be staged | Correctly deferred behind the data prerequisite |
| 150–200 epoch ceiling with plateau stopping | Maximum 200; all runs plateaued in 21–36 epochs | No time-limited or epoch-limited histories |
| Full long rollout | One temporal output bundle | Rollout-prefixed metrics duplicate bundle metrics; no long-horizon CHF claim |
| Physical wall residuals | Released tutorial crop lacks explicit wall cells | `interior_edge_*` remains an outer-released-grid metric, not a physical wall residual |
| Paper Table 9 parity | Custom five-field, 5→5 temporal-bundle task | Intentional project protocol; no Table 9 claim |

## Fail-closed verification

After training, an audit loaded every checkpoint on CPU with `torch.load(..., weights_only=True)` and checked it against its history. All **32/32** passed:

- status `completed`, device `mps`, and stop reason `validation_plateau`;
- result and checkpoint commit exactly `6dcede6e1f0495c0a298ff7c34cba3f71e4b583f`;
- checkpoint model/seed matching its filename;
- exact history length, best epoch, and best validation MSE agreement;
- full-grid factor `1`, modes `24`, maximum 200 epochs, and unlimited wall time;
- both benchmark JSON files referencing the single expected training commit.

The relevant test suite passed **15 tests**, and Ruff formatting/checks passed for the changed training and plotting code.

## Final project action

This run removes mode count, early stopping, seed count, and local GPU availability as explanations for the result. It does **not** remove data scarcity. The next infrastructure action is singular: place at least 5–10 official PB Subcooled training trajectories on external SSD or cluster storage, preserve trajectory-level splitting, and rerun this unchanged converged protocol. In parallel, CHF work may proceed only as a **T-FNO versus U-Net comparative evaluation**, with interface-temperature and conservation outcomes reported separately; there is no evidence basis for promoting T-FNO alone as the winner.
