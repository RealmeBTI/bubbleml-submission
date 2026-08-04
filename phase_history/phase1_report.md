# BubbleML Phase 1 report: official worked-example reproduction

Date: 2026-07-27 (Asia/Dhaka)

## Decision

**Phase 1 worked-example checkpoint: PASS. Phase 2 research gate: NO-GO.**

The upstream BubbleML notebook ran unchanged on the three official downsampled PB Subcooled trajectories. A deterministic three-seed FNO-vs-U-Net comparison also completed and shows a consistent U-Net advantage at the notebook's fixed 15-epoch budget. This is not yet a reproduction of the paper result: the upstream notebook describes itself as a simple, low-resolution example, provides only two training trajectories and one validation trajectory, has no held-out test trajectory, and stops while both loss curves are still improving.

Per the requested gate, Phases 2–4 were not started.

## Correction to the target claim

The supplied task says vanilla FNO is “roughly an order of magnitude worse” than U-Net on PB Subcooled BRMSE. The published BubbleML result does not support that statement. Table 9 reports PB Subcooled temperature BRMSE of 0.073 for UNetbench and 0.149 for vanilla FNO, a ratio of about 2.04×, not 10×. Table 10 reports 0.082 versus 0.214 for PB Saturated, about 2.61×. The paper attributes the trend cautiously to convolutional edge detection and the Fourier layer's implicit periodicity; it does not establish a single universal failure mechanism. See the [BubbleML paper](https://openreview.net/pdf?id=0Wmglu8zak) and [NeurIPS dataset page](https://papers.nips.cc/paper_files/paper/2023/hash/01726ae05d72ddba3ac784a5944fa1ef-Abstract-Datasets_and_Benchmarks.html).

The `boundary_rmse_outermost_grid` reported below is a transparent diagnostic over the outermost 48×48 grid cells. It is **not** the paper's BRMSE implementation, so its absolute values must not be compared to Tables 9–10.

## Provenance and data validation

Repository reviewed: official `HPCForge/BubbleML` clone under `third_party/BubbleML`. The upstream data documentation and SciML README were read before execution. The exact notebook was downloaded from the upstream `main` branch and preserved without edits.

| Role | File | Shape | SHA-256 |
|---|---|---:|---|
| train | `Twall-100.hdf5` | 201×48×48 | `5bf2539628c3595f39517c466f6971da76f137358771592c14ad1a5881e4d1bf` |
| train | `Twall-106.hdf5` | 201×48×48 | `4308e5be884c3edcf301e9c12bff8d499d53729be3820aa18e255a5152fbd004` |
| validation | `Twall-103.hdf5` | 201×48×48 | `25b305661dee59cf5df49eb2563a4ed08f79664ba377e57877fcda5a948956dd` |

Each HDF5 file was opened with `h5py`; all expected keys were present: `temperature`, `pressure`, `velx`, `vely`, `dfun`, `x`, `y`, and runtime-parameter groups. The task is one-step temperature prediction from current temperature, x-velocity, and y-velocity. It does not predict pressure, velocity, or phase fraction.

The validated micro-dataset is stored at `data/bubbleml/official_example/`. Training used an identical checksum-verified staging copy in `/private/tmp` to prevent iCloud hydration from contaminating timings.

## Official notebook run

The unmodified notebook completed successfully:

- train pairs: 400; validation pairs: 200
- train batches: 100; validation batches: 50
- batch size: 4; workers: 0
- FNO: modes 16×16, hidden channels 64, four Fourier layers
- optimizer: AdamW, learning rate 1e-4
- epochs: 15
- device: CPU, exactly as set by the notebook
- notebook-reported trainable parameter elements: 2,410,433

Artifacts:

- [`experiments/phase1_official/upstream_notebook/pytorch_training.ipynb`](experiments/phase1_official/upstream_notebook/pytorch_training.ipynb)
- [`experiments/phase1_official/upstream_notebook/pytorch_training.executed.ipynb`](experiments/phase1_official/upstream_notebook/pytorch_training.executed.ipynb)
- [`experiments/phase1_official/upstream_notebook/loss_curve.png`](experiments/phase1_official/upstream_notebook/loss_curve.png)
- [`experiments/phase1_official/upstream_notebook/sample_prediction.png`](experiments/phase1_official/upstream_notebook/sample_prediction.png)

## Fair comparison configuration

The logged comparison mirrors the notebook's split, preprocessing, loss, optimizer, learning rate, batch size, epoch budget, and CPU device.

| Item | FNO | U-Net |
|---|---:|---:|
| architecture | Neuraloperator FNO | 3-level encoder/decoder + bottleneck |
| width | hidden 64 | base channels 36 |
| layers/modes | 4; 16×16 modes | two 3×3 convolutions per block |
| trainable tensor elements (`numel`) | 2,410,433 | 2,436,733 |
| real scalar degrees of freedom | 4,769,729 | 2,436,733 |

The conventional PyTorch parameter count is matched within 1.1%. Because FNO spectral parameters are complex, counting real and imaginary components separately reveals a 1.96× FNO capacity advantage. Both counts are reported to avoid a misleading “matched capacity” claim.

This exact upstream reproduction uses width 64 and batch 4, not the requested custom width 32 and batch 16–32. That deviation is deliberate: changing them would no longer run the official example as-is. The separate five-field pipeline could not be scaled in this run because macOS had offloaded its source files to iCloud and hydration did not complete.

Runtime deviations from the upstream reproducibility environment:

- macOS arm64, Python 3.12, PyTorch 2.13.0, neuraloperator 2.0.0
- CUDA unavailable
- MPS was neither built nor available in this PyTorch runtime; all training used CPU
- upstream documentation describes Linux/NVIDIA runs with the repository's Python 3.9/CUDA environment

## Three-seed fixed-budget results

Seeds: 7, 42, 123. Best validation checkpoint within 15 epochs was used.

| Seed | FNO MSE | U-Net MSE | FNO boundary RMSE | U-Net boundary RMSE |
|---:|---:|---:|---:|---:|
| 7 | 0.00176489 | 0.00137769 | 0.0926532 | 0.0857599 |
| 42 | 0.00174507 | 0.00135595 | 0.0924036 | 0.0850557 |
| 123 | 0.00177365 | 0.00143424 | 0.0926095 | 0.0886843 |
| mean | **0.00176120** | **0.00138929** | **0.0925554** | **0.0865000** |
| 95% t CI | [0.00172483, 0.00179758] | [0.00128890, 0.00148969] | [0.0922244, 0.0928865] | [0.0817201, 0.0912799] |

At this budget U-Net has 21.1% lower mean MSE and 6.5% lower mean boundary RMSE. The paired mean MSE difference (FNO minus U-Net) is 0.0003719 with a 95% t interval [0.0003020, 0.0004419]. With only three pairs, the exact two-sided Wilcoxon signed-rank p-value is 0.25; therefore the result is a consistent pilot trend, not a robust significance claim. A parametric paired t-test gives p=0.0019, but its normality assumption cannot be assessed with n=3 and it should not drive the decision.

Neither model plateaued by epoch 15. For seed 42, FNO validation MSE continued from 0.0017765 at epoch 14 to 0.0017451 at epoch 15; U-Net continued from 0.0014015 to 0.0013559. The result is fixed-budget, not convergence-qualified.

Per-run artifacts follow the required layout:

- `experiments/phase1_official/{fno,unet}_seed_{7,42,123}/config.yaml`
- `experiments/phase1_official/{fno,unet}_seed_{7,42,123}/results.json`
- `experiments/phase1_official/{fno,unet}_seed_{7,42,123}/best.pt`
- seed-42 loss curves and three validation examples in the corresponding directories

The seed-7 and seed-123 `results.json` files marked `recovered_after_logger_interruption` were recomputed from the already-saved best checkpoints after an iCloud-blocked provenance call. Their weights and metrics are intact; their in-memory epoch histories were not recoverable. The seed-42 histories are complete.

## Conditional rollout

The notebook is a one-step model. To test horizons greater than one without inventing velocity forecasts, temperature was rolled autoregressively while supplying the true future velocity fields. This is a **conditional rollout**, not a fully coupled forecast. Results average three starts (30, 80, 130), three seeds, and the validation trajectory.

| Horizon | FNO RMSE | U-Net RMSE | FNO boundary RMSE | U-Net boundary RMSE |
|---:|---:|---:|---:|---:|
| 1 | 0.03931 | 0.03543 | 0.09082 | 0.08833 |
| 5 | 0.05850 | 0.04735 | 0.12060 | 0.09468 |
| 10 | 0.06551 | 0.06539 | 0.12351 | 0.11063 |

The global gap nearly disappears by horizon 10, while FNO retains a 11.6% higher boundary RMSE. This supports further boundary-focused diagnosis but does not identify Gibbs ringing by itself.

Visual inspection of the three horizon-10 samples shows strong smoothing in both models. FNO produces a broader diffuse background and larger wall-adjacent error; U-Net generally localizes the heated plume and wall region more sharply. There is no clear alternating overshoot/undershoot band in these temperature plots, so the observed failure is more consistent with over-smoothing plus boundary mismatch than with visually proven Gibbs ringing. A signed-error profile and spectrum are still required for a Gibbs diagnosis.

Artifacts:

- [`experiments/phase1_official/rollout_results.json`](experiments/phase1_official/rollout_results.json)
- [`experiments/phase1_official/rollout_h10_examples.png`](experiments/phase1_official/rollout_h10_examples.png)
- [`experiments/phase1_official/fno_seed_42/validation_examples.png`](experiments/phase1_official/fno_seed_42/validation_examples.png)
- [`experiments/phase1_official/unet_seed_42/validation_examples.png`](experiments/phase1_official/unet_seed_42/validation_examples.png)

## What this checkpoint cannot establish

1. It is validation-only. There is no independent official-example test trajectory.
2. It predicts temperature only. Phase-fraction interface continuity, velocity/pressure errors, divergence, energy conservation, and conservation-weighting artifacts are not measurable from these outputs.
3. Fifteen epochs did not reach a plateau.
4. Three seeds are insufficient for a reliable nonparametric significance result.
5. The paper's preprocessing, full training set, evaluation masks, BRMSE code, and higher-resolution setup were not reproduced by the simple notebook.
6. Visuals can reveal localized error, but this run does not contain the spectral/edge diagnostics required to classify it as Gibbs ringing.

## Environment failure and traceability

The workspace resides in macOS Documents/iCloud. During execution, macOS marked the existing benchmark source, virtual environment, prior smoke artifacts, and even newly written small text files as `compressed,dataless`. Reads then blocked indefinitely. `brctl download` requests did not hydrate those files in time. To avoid corrupt timing and partial data, the exact upstream files and a clean virtual environment were staged in `/private/tmp`; durable experiment artifacts were written back to the workspace.

Git metadata was also offloaded, so a commit hash could not be read reliably. Logs record this limitation rather than fabricating a revision. No commit was created because the workspace contained unrelated user changes.

## Required next action before Phase 2

Move or clone the project to a non-iCloud local directory (or disable “Optimize Mac Storage” for this folder), restore an independent test split from the full official PB Subcooled dataset, and rerun to plateau with at least five seeds. Then execute the existing five-field benchmark unchanged and compare its exact GWRMSE, boundary, interface, and conservation metrics. Until those conditions are met, **do not proceed to physics-informed remedies or claim the paper gap is reproduced**.
