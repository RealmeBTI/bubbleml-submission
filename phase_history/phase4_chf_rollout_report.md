# Phase 4: CHF/dry-spot rollout evaluation

## Outcome

The available `Twall-100.hdf5` trajectory does **not** contain a sustained ground-truth crossing under the declared dry-area precursor rule, so this run cannot measure CHF lead time. It is a stable/high-heat-flux **false-positive test** and a methodology demonstration, not a validated CHF predictor.

Both fully autoregressive models produce false alarms:

- **T-FNO:** first false crossing at rollout step 11 (source timestep 45), 6 total alarm frames, two sustained episodes, longest episode 3 frames.
- **U-Net:** first false crossing at rollout step 25 (source timestep 59), 108 total alarm frames, seven sustained episodes, longest episode 39 frames.

T-FNO gives the better dry-area signal over the complete 164-step rollout: cumulative MAE `0.07123` versus U-Net's `0.13764`. Its alarm is earlier but transient; U-Net develops a large persistent positive vapor-coverage bias. Neither is ready to serve as a CHF alarm: both falsely trigger, both predict alpha outside its physical `[0,1]` range, and neither has been tested on a trajectory with a verified stable-to-CHF transition.

The Phase 1 Pareto tradeoff remains. T-FNO's interface advantage does not become a uniform long-rollout interface win, and U-Net's one-step conservation advantage does not guarantee better long-horizon dry-area tracking.

## Reproducibility

| Item | Value |
|---|---|
| Evaluation code commit | `9bcebe026b55f087f331f127690e2f9b9b68da71` |
| Training/checkpoint commit | `6dcede6e1f0495c0a298ff7c34cba3f71e4b583f` |
| Evaluator | [`bubbleml_benchmark/chf_rollout.py`](bubbleml_benchmark/chf_rollout.py) |
| Machine/backend | Apple M2, MPS |
| Full result | [`rollout_results.json`](benchmark_results/phase4_chf_rollout/rollout_results.json) |
| Horizon CSV | [`horizon_metrics.csv`](benchmark_results/phase4_chf_rollout/horizon_metrics.csv) |
| Centerpiece plot | [`dry_area_fraction_rollout.png`](benchmark_results/phase4_chf_rollout/dry_area_fraction_rollout.png) |

Checkpoint selection used validation loss, not held-out rollout behavior:

| Model | Selected seed | Best validation MSE | Best epoch | Checkpoint SHA-256 |
|---|---:|---:|---:|---|
| T-FNO | 9999 | 0.451594 | 21 | `f85e4b3811e721abed3ede47b3b9701b2525aad36c60ddb59d766c7fb0738bab` |
| U-Net | 7 | 0.439600 | 28 | `58173aca6b36dbcb2b748a81549435b7288bbbd1cb91dacf97a25d9746feb3d8` |

These are the lowest validation-MSE checkpoints among the eleven available seeds for each model. This avoids selecting a model seed on the same held-out trajectory used here.

## Dry-area/CHF proxy

The official BubbleML documentation says fields are stored as `time × y × x`, row 0 is the released cell immediately above the heater, the heater spans the bottom boundary, and `dfun > 0` identifies vapor. It also states that physical boundary cells are not present. See the [official data documentation](https://github.com/HPCForge/BubbleML/blob/main/bubbleml_data/DOCS.md).

The protocol is fixed as follows:

1. Convert the existing `alpha_vapor_mask = (dfun > 0)` channel to vapor occupancy with `alpha > 0.5`.
2. Compute dry-area fraction across rows `0:4`, the first four released grid rows above the heater.
3. Use the median of the first 20 ground-truth forecast frames as baseline: `0.24479`.
4. Define the event threshold as `max(0.10, baseline + 0.10) = 0.34479`.
5. Require at least three consecutive frames at or above the threshold. Isolated spikes do not count.

This threshold is deliberately simple and protocol-defining. It is not calibrated to measured CHF labels.

## Does Twall-100 contain CHF?

The local source is the official downsampled PB Subcooled tutorial trajectory:

| Property | Recorded value |
|---|---|
| File | `official_example/Twall-100.hdf5` |
| SHA-256 | `5bf2539628c3595f39517c466f6971da76f137358771592c14ad1a5881e4d1bf` |
| Wall temperature from filename | 100 °C |
| Source frames evaluated | timesteps 30–198 (169 frames) |
| Initial history | timesteps 30–34 |
| Fully autoregressive forecast | timesteps 35–198 (164 steps) |
| Wall heat-flux time series | **absent** |

The HDF5 stores a constant normalized wall-temperature boundary and does not store a wall-heat-flux time series. The BubbleML paper identifies FC-72 saturation temperature as 58 °C and its Figure 5 boiling curve places the subcooled normalized heat-flux maximum around `Twall − Tsat ≈ 50 °C`; `Twall=100 °C` gives about 42 °C wall superheat. Reading the figure, this trajectory is plausibly on the high, rising part of the boiling curve but below the displayed maximum. This is an inference, not a heat-flux measurement. See the [BubbleML paper, Figure 5](https://papers.nips.cc/paper_files/paper/2023/file/01726ae05d72ddba3ac784a5944fa1ef-Paper-Datasets_and_Benchmarks.pdf).

The signal agrees with the conservative interpretation: ground truth reaches a maximum dry fraction of `0.38542`, but only three frames in total exceed `0.34479`, the longest consecutive run is two frames, and there is no sustained event. Therefore this is not evidence of an actual CHF transition.

## Centerpiece: dry-area fraction over time

![Ground truth, T-FNO, and U-Net dry-area fraction across the full autoregressive rollout](benchmark_results/phase4_chf_rollout/dry_area_fraction_rollout.png)

Every predicted five-frame bundle is fed back verbatim as the next five-frame input. No future ground-truth velocity, temperature, phase, or pressure-gradient field is injected. Predicted alpha is not clipped before feedback.

## Alarm and false-positive analysis

| Series | First sustained crossing | Frames ≥ threshold | Longest run | Sustained episodes | Interpretation |
|---|---:|---:|---:|---:|---|
| Ground truth | none | 3/164 | 2 | 0 | no protocol event |
| T-FNO | step 11 / source 45 | 6/164 | 3 | 2 | early, brief false alarms |
| U-Net | step 25 / source 59 | 108/164 | 39 | 7 | later but persistent false alarm |

Because ground truth never crosses, neither alarm has a valid lead time. Calling step 11 or step 25 “early warning” would be incorrect; both are false positives.

## Dry-signal accuracy by horizon

The exact error is measured at the named rollout step. Cumulative MAE uses all forecast frames from step 1 through that horizon.

| Horizon | Ground truth | T-FNO prediction | T-FNO exact abs. error | T-FNO cumulative MAE | U-Net prediction | U-Net exact abs. error | U-Net cumulative MAE |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.26042 | 0.24479 | 0.01562 | **0.00729** | 0.27083 | **0.01042** | 0.02396 |
| 10 | 0.13542 | 0.28125 | 0.14583 | **0.04375** | 0.24479 | **0.10938** | 0.04479 |
| 20 | 0.21875 | 0.20312 | **0.01562** | 0.07161 | 0.23438 | **0.01562** | **0.05026** |
| 40 | 0.22917 | 0.31771 | **0.08854** | **0.07005** | 0.36979 | 0.14062 | 0.07370 |
| 80 | 0.20312 | 0.32292 | 0.11979 | **0.07155** | 0.26042 | **0.05729** | 0.09740 |
| 160 | 0.22396 | 0.32812 | **0.10417** | **0.07132** | 0.36979 | 0.14583 | 0.13669 |
| 164 | 0.27604 | 0.31250 | **0.03646** | **0.07123** | 0.46875 | 0.19271 | 0.13764 |

T-FNO tracks the long-horizon signal substantially better in aggregate, even though its first threshold crossing occurs earlier. U-Net's predicted dry fraction becomes persistently too high after roughly step 40.

## Standard five-field accuracy at each horizon

These are exact-frame metrics, not cumulative means. Lower is better. Their oscillation reflects the strongly time-dependent target and five-frame bundle cadence; cumulative stability is reported separately below.

| Model | Horizon | Relative L2 | RMSE | GWRMSE | Temperature GWRMSE | Alpha GWRMSE | Mass-conservation MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| T-FNO | 5 | 0.4866 | 3.5720 | 5.7151 | **10.5168** | 0.4080 | 0.2142 |
| U-Net | 5 | **0.4229** | **3.1040** | **5.4158** | 10.6978 | **0.3867** | **0.1589** |
| T-FNO | 10 | 0.7392 | 7.3228 | 10.6019 | 17.6065 | 0.5093 | 0.1707 |
| U-Net | 10 | **0.7056** | **6.9902** | **10.1441** | **17.1083** | **0.4817** | **0.1568** |
| T-FNO | 20 | **0.4799** | **4.0292** | **6.6789** | **11.8069** | **0.3969** | **0.1222** |
| U-Net | 20 | 0.5718 | 4.8011 | 7.5325 | 13.6109 | 0.4383 | 0.1294 |
| T-FNO | 40 | **0.7629** | **15.2612** | **16.3364** | **14.2150** | **0.4586** | **0.0995** |
| U-Net | 40 | 0.7882 | 15.7676 | 16.7804 | 14.5996 | 0.4721 | 0.1254 |
| T-FNO | 80 | 1.3242 | 6.2092 | 8.5224 | 14.0590 | 0.5045 | **0.1102** |
| U-Net | 80 | **1.1602** | **5.4400** | **7.3353** | **12.7405** | **0.4772** | 0.1348 |
| T-FNO | 160 | 1.2705 | 19.5086 | 21.2007 | **14.5802** | **0.4357** | **0.1184** |
| U-Net | 160 | **1.2350** | **18.9629** | **21.1056** | 17.8265 | 0.4762 | 0.1318 |
| T-FNO | 164 | **0.8009** | **18.3884** | **19.5085** | 14.7225 | **0.4014** | **0.1110** |
| U-Net | 164 | 0.8331 | 19.1282 | 20.1505 | **13.9996** | 0.4312 | 0.1281 |

## Interface accuracy and rollout stability

| Model | Horizon | Interface temperature RMSE | Interface jump MAE |
|---|---:|---:|---:|
| T-FNO | 5 | 13.0798 | **14.6875** |
| U-Net | 5 | **12.7893** | 16.5041 |
| T-FNO | 10 | 19.1350 | 16.7491 |
| U-Net | 10 | **18.6352** | **16.0651** |
| T-FNO | 20 | **14.8412** | **19.2766** |
| U-Net | 20 | 17.9739 | 19.6601 |
| T-FNO | 40 | **17.8996** | **14.7759** |
| U-Net | 40 | 18.0750 | 15.3301 |
| T-FNO | 80 | 17.8325 | 16.7270 |
| U-Net | 80 | **15.1619** | **16.3993** |
| T-FNO | 160 | 20.9527 | 20.5747 |
| U-Net | 160 | **19.4622** | **20.5682** |
| T-FNO | 164 | 20.6789 | 15.6538 |
| U-Net | 164 | **15.3630** | **15.2780** |

Phase 1's statistically significant T-FNO interface advantage does not persist uniformly frame by frame in this rollout. T-FNO wins both interface metrics at horizons 20 and 40, the jump metric at horizon 5, and loses at later selected endpoints. A single trajectory and correlated rollout frames do not support a new significance claim.

For stability, cumulative means through the full 164 steps are:

| Model | Cumulative RMSE | Cumulative GWRMSE | Cumulative mass MAE | Finite values | Predicted alpha range |
|---|---:|---:|---:|---|---|
| T-FNO | **9.3727** | 11.8618 | **0.11963** | 100% | `[-0.157, 1.408]` |
| U-Net | 9.4320 | **11.6304** | 0.12219 | 100% | `[-0.108, 1.417]` |

U-Net begins with clearly lower cumulative mass error (`0.1488` versus `0.2139` through five steps), consistent with Phase 1, but that advantage erodes and reverses slightly over the full rollout. U-Net retains the slightly lower cumulative GWRMSE; T-FNO has slightly lower cumulative RMSE and mass error. Both remain numerically finite, but both leave the physical alpha range because the training objective did not impose a bounded phase output. No clipping was applied, because clipping would conceal rather than diagnose that failure mode.

## Synthesis

- **Does T-FNO's interface advantage translate to CHF-signal tracking?** Partly. T-FNO halves full-rollout dry-signal MAE and avoids U-Net's persistent high-vapor bias. Its raw interface-temperature advantage is intermittent, not universal.
- **Does T-FNO's Phase 1 mass weakness cause faster divergence?** Not on this trajectory. It is worse initially, but its cumulative mass error falls below U-Net's by the end. This is descriptive, not statistically generalizable.
- **Does U-Net conservation make rollout more stable?** It helps early and U-Net retains slightly better cumulative GWRMSE, but it does not protect the dry-area signal: U-Net spends 108/164 frames above the false-alarm threshold.
- **Is either model a validated CHF predictor?** No. T-FNO is the better dry-area tracker here, but both false alarm and there is no true event on which to measure detection or lead time.

## What is required for validated CHF forecasting

The next evaluation needs a held-out, high-resolution trajectory that:

1. begins in stable nucleate/subcooled boiling;
2. spans a documented transition into sustained vapor-film coverage;
3. includes synchronized wall heat flux or enough boundary temperature-gradient information to label the CHF maximum independently of model output;
4. retains explicit heater-adjacent resolution rather than only the 48×48 tutorial crop;
5. provides multiple event and non-event trajectories for calibrated threshold selection, lead-time distributions, false-alarm rate, missed-event rate, and uncertainty intervals.

Until those data exist, the present threshold, false-positive counts, and dry-area curves must remain labeled as a protocol demonstration. The implementation is ready to run unchanged on such a trajectory; the missing piece is an independently verified CHF label, not another Phase 1 architecture comparison.
