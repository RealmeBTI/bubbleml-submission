# Tier-1 Track A/B closeout: legacy data and conservation-targeted hybrid

## Executive result

Both requested tracks reached an evidence-bearing result.

- **Track A completed acquisition and verification.** A Google Colab runtime downloaded the official 10.35 GiB legacy PB-Subcooled archive at about 39 MiB/s after a bounded 100 MiB rate gate completed in 3 seconds. The archive SHA-256 is `2eba140d74cbb7b01a55f0684227dea94306aea516a0f864831485d31d25f655`. All ten native 384 x 384 trajectories were extracted, schema-checked, size-checked, and individually checksummed. They are currently staged in the Colab runtime's ephemeral `/content` storage; the reproducible notebook is also checked into this repository.
- **Track B passed its sole predeclared confirmatory criterion.** With `lambda_div=0.10` frozen before the confirmatory sweep, the freshly trained divergence-penalized local-global hybrid was non-inferior to U-Net on mass-conservation MAE over the same 11 seeds (`p=.000976`, paired 95% bootstrap interval for hybrid minus U-Net `[-.02845,-.01331]`, entirely below the fixed `+.00829` margin). Its mean mass MAE was also numerically lower (`.14499` versus `.16586`). Superiority was not the predeclared claim, so the formal conclusion remains non-inferiority; the negative interval is strong descriptive evidence in the favorable direction.
- **The interface gain was not sacrificed.** The divergence hybrid's mean interface-temperature RMSE/jump MAE were `14.9472/15.5896`, compared with `15.0807/15.7756` for T-FNO and `15.5826/16.2070` for U-Net. Against the zero-penalty hybrid, the paired changes were `+.02996` and `-.01535`; both intervals included zero. No interface regression was established.
- **The Phase-1 multi-trajectory and resolution rerun remains pending.** Acquisition was prioritized, as requested. The Colab session supplied a CPU runtime despite the T4 selection, so native-resolution three-model training was not started there. The current scientific architecture result therefore still comes from the existing 48 x 48 tutorial split; the newly staged trajectories remove the access obstacle but do not by themselves establish cross-trajectory or cross-resolution generalization.

## Track A: cloud-side official archive acquisition

### Cloud gate and transfer

The live Colab notebook is `bubbleml_cloud_fetch.ipynb` at:

`https://colab.research.google.com/drive/1jRE-esu_IsafhnQjFH7ru95Q1PJUrcUh`

The checked-in, rerunnable copy is `notebooks/bubbleml_cloud_fetch.ipynb`.

The first cloud attempt used Kaggle. The signed-in notebook was created successfully, but Kaggle's **Internet** control was disabled until phone verification. Its 100 MiB probe therefore failed at DNS resolution and reported zero bytes; this is an account-feature restriction, not a slow BubbleML endpoint. The Kaggle working volume also exposed only about 19.5 GiB, less than the archive plus all extracted trajectories.

Colab was then tested before the full transfer:

| Gate | Result |
|---|---:|
| Runtime free space before download | 94,203,817,984 bytes |
| Bounded probe | 104,857,600 bytes |
| Probe elapsed time | 3 s |
| Probe effective rate | 33.3 MiB/s |
| Required minimum rate | 1 MiB/s |
| Full archive elapsed time | 270 s |
| Full archive size | 11,108,940,120 bytes |
| Full-transfer average shown by curl | about 39.3 MiB/s |
| Archive SHA-256 | `2eba140d74cbb7b01a55f0684227dea94306aea516a0f864831485d31d25f655` |
| Extraction elapsed time | 222 s |
| Free space after extraction | about 62 GiB |

The cloud transfer was roughly four orders of magnitude faster than the previously measured local 4.8 KiB/s path and completed without proxying data through the local Mac.

### Ten-trajectory manifest

Every HDF5 file is exactly `1,659,787,108` bytes. Each contains 201 frames at native `384 x 384` resolution for `velx`, `vely`, `pressure`, `temperature`, `dfun`, `x`, and `y`, plus the expected integer and real runtime-parameter arrays. This is a five-physical-field source after the existing phase transformation (`alpha_vapor_mask = dfun > 0`).

| Trajectory | SHA-256 |
|---|---|
| `Twall-79.hdf5` | `c550dab2e2d5db4ecb7ccc159aefba2a43ab61c50d6d22a0a5322d2a45ad07df` |
| `Twall-81.hdf5` | `16b6cae48b50cb06a202e0f2c56585caf66eb6919e060b61dc7902026ab84452` |
| `Twall-85.hdf5` | `4f761caf8efcd66f93bcb55c36eea72876d83f85b8b30526a1b48dfeeb7e8dda` |
| `Twall-90.hdf5` | `35c859305795fda3a59ea16343d75a611ef4e89c7bacfa05c273b47bcc2d7240` |
| `Twall-95.hdf5` | `75809930d09d013024a76c0695f28f02c6785183e6d402285486fba334b65338` |
| `Twall-98.hdf5` | `1c3e4f23908ce6137d88abb8beb438ac08996ffbf191c6d91935d606bafdeb15` |
| `Twall-100.hdf5` | `8529a1b55613449dbbf99c936ce5f8308abfac92fe856891a9b337bd7f2e949e` |
| `Twall-103.hdf5` | `4ebc2f95c61fa64b4422f51603a35f19a55add15093fdee435db0558d4d458e1` |
| `Twall-106.hdf5` | `1b035a9cd8c9b765035bfe88ba2993aee96c52e5df6a8e2c4d32f51b8ca8db45` |
| `Twall-110.hdf5` | `874a07784d0120b402438d69bf66dd04191bd76ac1eb4b8151ad2ddec55134fd` |

The archive and extracted files are in ephemeral Colab runtime storage (`/content/pool-boiling-subcooled-fc72-2d.tar.gz` and `/content/bubbleml/PoolBoiling-SubCooled-FC72-2D`). Runtime disconnection will remove them. The checked-in notebook preserves the exact, rate-gated acquisition and verification procedure, but not the 27.7 GB cloud payload.

### Fixed dry-area protocol across all trajectories

The scan reused the existing rule without looking at outcomes first:

1. form the binary vapor mask `dfun > 0`;
2. compute vapor-covered fraction in rows `0:4`;
3. set the per-trajectory threshold to `max(.10, median(first 20 frames)+.10)`; and
4. require at least three consecutive frames at or above that threshold.

| Twall | Baseline | Threshold | Maximum | Frames >= threshold | Longest run | First sustained frame |
|---:|---:|---:|---:|---:|---:|---:|
| 79 | .285807 | .385807 | .358073 | 0 | 0 | none |
| 81 | .301432 | .401432 | .453125 | 54 | 36 | 50 |
| 85 | .333984 | .433984 | .461589 | 5 | 4 | 134 |
| 90 | .332031 | .432031 | .438151 | 4 | 3 | 57 |
| 95 | .352539 | .452539 | .420573 | 0 | 0 | none |
| 98 | .333333 | .433333 | .420573 | 0 | 0 | none |
| 100 | .327474 | .427474 | .483724 | 6 | 4 | 119 |
| 103 | .325521 | .425521 | .420573 | 0 | 0 | none |
| 106 | .312500 | .412500 | .420573 | 1 | 1 | none |
| 110 | .327474 | .427474 | .429688 | 1 | 1 | none |

Twall 81, 85, 90, and 100 satisfy the protocol's sustained-crossing rule. This does **not** establish a physical CHF transition. The candidates are not concentrated at the highest wall temperatures—Twall 110 has only one crossing frame—and the files do not supply an independent CHF label or synchronized wall heat-flux series. The correct conclusion is that the archive contains four sustained **proxy** events suitable for event/non-event stress tests, not four validated CHF cases.

### Phase-1 trajectory/resolution rerun status

Not run in this closeout. The acquisition, integrity verification, and independent-trajectory proxy scan consumed the cloud session, and the allocated runtime remained CPU-backed (`nvidia-smi` unavailable) after selecting T4. Starting native 384 x 384 training there would have produced an incomplete, non-comparable result. The next run should persist or re-fetch the archive, split by Twall rather than temporal windows, and compare the unchanged T-FNO, U-Net, zero-penalty hybrid, and divergence hybrid at 96 x 96 and 384 x 384. Independent trajectories should be prioritized over more seeds.

## Track B: spectral-divergence conservation intervention

### Implementation

`hybrid_div` uses the already-tested local-global Tucker-FNO architecture and adds the requested physical-space velocity-divergence term computed through full two-dimensional Fourier derivatives:

`L_div = mean(abs(IFFT(i*kx*FFT(u) + i*ky*FFT(v))))`

The implementation decodes normalized predictions before extracting the velocity channels, reshapes all five future frames, uses per-sample physical `dx` and `dy`, and keeps the validation checkpoint criterion as data MSE rather than the penalized objective. Training uses `L_total = L_data + lambda_div * L_div`. The MPS path explicitly casts spectral spacing tensors to float32. A positive lambda is required for `hybrid_div`, and the penalty cannot silently affect the other models.

Direct tests cover model construction, zero divergence for periodic cross-axis velocity fields, gradient flow only into velocity channels, lambda validation, and the analyzer's exact 11-seed requirement.

### Pilot and frozen lambda

The pilot protocol was committed before divergence-penalty training. Candidates `.01`, `.03`, and `.10` used only seeds 42 and 100 and only training/validation outcomes. Eligibility required mean best validation MSE no more than 5% above the zero-penalty hybrid reference (`.45300846`; ceiling `.47565888`). Among eligible values, the lowest validation spectral divergence was selected.

| `lambda_div` | Mean best validation MSE | Mean validation spectral divergence | Eligible |
|---:|---:|---:|---|
| .01 | .45283415 | .21858509 | yes |
| .03 | .45223404 | .18549221 | yes |
| .10 | .45141906 | .13581720 | yes |

`lambda_div=.10` was frozen and committed before the 11-seed sweep. It reduced pilot validation divergence by 37.9% versus `.01` without triggering the data-fit guard.

### Confirmatory mass-conservation result

The confirmatory sweep trained fresh models for seeds `42, 100, 1234, 2025, 9999, 7, 17, 314, 2718, 4242, 7777`. All runs used the established Phase-1 split and MPS policy and stopped through the validation-plateau rule.

The sole predeclared test was lower-is-better mass-conservation MAE versus U-Net with fixed margin `.008292845428963615`, deterministic 10,000-sample paired bootstrap interval, and exact lower-tail sign-flip inference. A one-test Holm family leaves the p-value unchanged.

| Quantity | Result |
|---|---:|
| Divergence hybrid mean mass MAE | .14499348 |
| U-Net mean mass MAE | .16585691 |
| Hybrid minus U-Net | -.02086343 |
| Paired bootstrap 95% interval | `[-.02845424,-.01331148]` |
| Fixed non-inferiority margin | +.00829285 |
| Exact / Holm non-inferiority p | .00097609 |
| Predeclared outcome | **non-inferior** |

The upper confidence bound is more than `.0216` below the allowed margin. The point estimate and complete interval also favor the hybrid, but superiority was not the predeclared one-test claim. In the unchanged broad benchmark's two-sided complete-metric family, mass MAE also favored the divergence hybrid (raw exact `p=.00244`, Holm `p=.04880`); that is supporting, not a replacement for the predeclared result.

### Interface and aggregate safeguards

| Model | Mass MAE | Interface-T RMSE | Interface-T jump MAE | GWRMSE | RMSE |
|---|---:|---:|---:|---:|---:|
| divergence hybrid | .14499 | 14.94724 | 15.58959 | 11.10715 | 9.23930 |
| zero-penalty hybrid | .20462 | 14.91728 | 15.60494 | 11.12063 | 9.25387 |
| T-FNO | .21079 | 15.08070 | 15.77556 | 11.13385 | 9.23554 |
| U-Net | .16586 | 15.58260 | 16.20702 | 11.19084 | 9.18737 |

Relative to the zero-penalty hybrid, the divergence penalty changed interface-temperature RMSE by `+.02996` (95% paired bootstrap interval `[-.11819,+.17406]`) and jump MAE by `-.01535` (`[-.06768,+.03619]`). Neither interval establishes regression. Descriptively, both interface measures remain better than T-FNO and U-Net, while GWRMSE is the best of the four. Plain RMSE remains slightly worse than U-Net; the intervention does not produce uniform domination across every metric.

## Updated Tier-1 readiness table

| Critique | Previous status | Current evidence | Status now |
|---|---|---|---|
| Single-trajectory overfitting / no independent conditions | Open | Ten independent Twall trajectories are acquired and verified, but the Phase-1 model comparison has not yet been rerun across them. | **Partially resolved: data obstacle removed; generalization result pending** |
| Tutorial-only 48 x 48 resolution | Open | Ten native 384 x 384 sources are acquired, with an explicit 96/384 evaluation path, but no multi-resolution model result yet. | **Partially resolved: native data staged; resolution test pending** |
| No actual CHF transition | Open and correctly scoped | Four trajectories satisfy the fixed sustained dry-area proxy; the non-monotonic Twall pattern and absent heat-flux/CHF labels prevent calling them physical CHF events. | **Open, with better proxy-event coverage** |
| Hybrid does not match U-Net conservation | Failed for conv-only hybrid | Fresh 11-seed divergence hybrid passes the fixed mass non-inferiority test and is numerically better, without an established interface regression. | **Resolved on the existing Phase-1 split** |

## Reproducibility artifacts

- Cloud acquisition notebook: `notebooks/bubbleml_cloud_fetch.ipynb`
- Pilot predeclaration: `tier1_divergence_pilot_protocol.md`
- Frozen lambda record: `tier1_divergence_lambda_selection.md`
- Confirmatory checkpoints: `checkpoints/phase1_gpu_decisive/hybrid_div_seed_*.pt`
- Training histories: `experiments/tier1_div_n11/`
- Full 44-run benchmark: `benchmark_results/tier1_div_n11/benchmark_results.json`
- Single-criterion result: `benchmark_results/tier1_div_n11/divergence_noninferiority.json`
- Implementation: `bubbleml_benchmark/paper_train.py`, `bubbleml_benchmark/paper_models.py`, and `bubbleml_benchmark/divergence_analysis.py`

## Final verification

- All four tracked test modules passed: **28 passed** in 15.42 seconds (`test_bubbleml_benchmark.py`, `test_chf_rollout.py`, `test_chf_rollout_stats.py`, and `test_paper_pipeline.py`). The only warning was that pytest could not write its cache under the read-restricted canonical checkout; it does not affect test execution.
- Unfiltered `pytest -q` was also attempted. Collection stopped on two unrelated, untracked local test files: `tests/test_geometry.py` imports the absent `adaptive_dd_pinn.config`, and `tests/test_v3_architecture.py` imports the absent `adaptive_dd_pinn.boundary_manager`. These files are not part of the tracked BubbleML suite and were preserved rather than rewritten or deleted.
- The checked-in notebook and both confirmatory JSON outputs parse successfully.
- The benchmark and non-inferiority JSON trees contain only finite numeric values.
- Exactly 11 `hybrid_div_seed_*.pt` checkpoints and 11 corresponding experiment directories exist, matching the predeclared seed set.
- The completed benchmark contains 44 evaluations: divergence hybrid, zero-penalty hybrid, T-FNO, and U-Net across the same 11 seeds.

## Claim boundary

The conservation-targeted hybrid breaks the earlier local-global hybrid's mass-conservation failure on the existing tutorial-scale split. It does not yet prove a universal architecture ranking, native-resolution generalization, or CHF forecasting. The archive acquisition makes the next decisive experiment feasible; only a trajectory-level 96/384 rerun and independently supported event labels can close those remaining claims.
