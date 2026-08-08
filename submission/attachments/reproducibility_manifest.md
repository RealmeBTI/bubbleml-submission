# Reproducibility Manifest and Supplementary Material Checklist

*This document maps the artifacts already generated across this project's development to what should be packaged and where, before submission. Convert this into the actual public repository structure described in the Data Availability Statement.*

## 1. Source data (do not re-upload; cite and checksum-reference only)

| Item | Role | Verification |
|---|---|---|
| `Twall-100.hdf5`, `Twall-103.hdf5`, `Twall-106.hdf5` | Tutorial-split train/val/test | SHA-256 checksums recorded in Methods §3.1 |
| Legacy 10-trajectory archive (`Twall-79...110`) | Cross-condition split source | Archive SHA-256 recorded in Methods §3.1 |

Do not re-host the raw BubbleML data files themselves unless the dataset's license explicitly permits redistribution — link to the official source and cite the checksums as verification that your copy matches the canonical release.

## 2. Code (public GitHub repository, referenced by DOI)

| Component | Contents |
|---|---|
| Data pipeline | Preprocessing, schema validation, trajectory-level split logic, HDF5 loaders for both tutorial and legacy-archive formats |
| Model definitions | FNO, T-FNO, F-FNO, U-Net, local-global hybrid, divergence-penalty hybrid, bounded-alpha output head |
| Training scripts | Full training loop, validation-plateau stopping rule, checkpoint saving/safe-loading (`weights_only=True`) |
| Evaluation scripts | Five-field benchmark metrics, interface/conservation metrics, autoregressive CHF-proxy rollout evaluator |
| Statistical analysis | Paired bootstrap, exact sign-flip test, Holm-Bonferroni correction (single unchanged implementation used throughout) |
| Plotting/figures | Loss curve, dry-area trace, Pareto-front, lambda-sensitivity, benchmark-workflow, and split-diagram generation scripts; field snapshots are declared unavailable |
| Tests | Full test suite covering architecture, serialization, and statistical protocol correctness |

## 3. Configuration and provenance (include in repository, reference in Supplementary)

For every experiment referenced in the manuscript, the repository should retain:
- `config.yaml` (exact hyperparameters used)
- `results.json` (full training history: per-epoch train/val loss, wall time, stop reason)
- Checkpoint file with recorded SHA-256, seed, and git commit hash
- Runtime environment record (Python/PyTorch version, CUDA/MPS availability, hardware)

This is available for the locally retained tutorial and intervention experiments. The compact cross-condition export lacks complete per-seed configs, histories, and checkpoints; this gap is documented in `ARTIFACT_GAPS.md` and must not be described as complete.

## 4. Figures (separate high-resolution files for journal upload)

| Figure | Source |
|---|---|
| Ground-truth vs. prediction field snapshots (multiple horizons) | Not included: cross-condition arrays/checkpoints and a compatible tutorial T-FNO/U-Net checkpoint pair are unavailable locally |
| Dry-area-fraction-over-time trace | Phase 4 rollout evaluation output |
| Pareto-front scatter (interface RMSE vs. mass MAE, all model variants, with bootstrap error bars) | Generated during manuscript polish phase |
| Lambda-sensitivity curve | Generated during divergence-penalty sensitivity analysis |
| Loss curves (training/validation, all models/seeds) | Generated at each training phase |

Export each at minimum 300 DPI (line-art figures like the sensitivity curve and Pareto front should be vector format — PDF or EPS — if the journal accepts it, since these will need to scale cleanly in print).

## 5. Tables for Supplementary Material (beyond what fits in the main manuscript)

- Full per-seed results (not just aggregate mean/CI) for every statistical comparison reported in the manuscript — reviewers may specifically request these to spot-check your bootstrap/sign-flip computations.
- Full lambda_div sensitivity table (all five tested values, all three guard metrics).
- Full computational-cost table (already compiled) with per-seed training times, not just means.

## 6. Statistical audit trail

Explicitly document, in a short supplementary note: the correction made to the sign-flip/Holm implementation (removal of an unnecessary Monte Carlo add-one correction, exclusion of compute-only metrics from the Holm family) and confirmation that all numbers reported in the final manuscript reflect the corrected implementation, not the earlier uncorrected one. This preempts a reviewer question and demonstrates the same transparency already present throughout the project.

## 7. What NOT to include in the direct journal upload (host externally instead)

- Raw model checkpoints beyond what's needed to verify one representative result per major claim (host the complete set on Zenodo/GitHub, link don't upload, if journal file-size limits are a concern).
- Full per-epoch logs for all 20+ training runs (summarize in the repository, don't inflate the journal's own supplementary PDF).

## 8. Final pre-submission verification pass

Before uploading anything:
1. Click every link in the manuscript and supplementary material yourself, from a fresh/incognito browser session, to confirm nothing is broken or access-restricted.
2. Re-run at least one full result end-to-end from the public repository (ideally on a clean machine or fresh cloud instance) to confirm the reproducibility instructions actually work as written — this is the single most common reason reviewers flag reproducibility concerns, and it's fully within your control to catch before submission.
3. Confirm every SHA-256 checksum quoted in the manuscript matches the actual file in the archived repository.
