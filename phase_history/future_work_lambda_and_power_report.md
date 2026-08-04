# Future-work extension report: lambda range and cross-condition power

**Status:** protocol frozen; execution is intentionally non-blocking and is not used to
change the current manuscript.  The exploratory runs in this file must not be pooled
with the confirmatory numbers in `paper_methods_results_draft.md` or
`paper_narrative_draft.md`.

**Date:** 2026-08-02 (Asia/Dhaka)

## Scope and separation rule

This report implements the two extensions requested after the completed multi-trajectory
benchmark:

1. Extend the divergence-penalty range and pilot it with at least five paired seeds.
2. Increase cross-condition power with held-out trajectories and a full four-model
   comparison.

The existing manuscript result remains frozen at the previously selected
`lambda_div = 0.30`.  Any future-work run is written to new directories (suggested
roots: `experiments/future_lambda_ext/`, `checkpoints/future_lambda_ext/`,
`benchmark_results/future_lambda_ext/`, `experiments/future_cross_condition/`, and
`benchmark_results/future_cross_condition/`).  A future-work result is not a replacement
for the existing result unless a later, separately pre-registered confirmatory run is
completed.

## Baseline that this extension is allowed to reference

The completed independent multi-trajectory benchmark used the official archive with
SHA-256
`2eba140d74cbb7b01a55f0684227dea94306aea516a0f864831485d31d25f655`, 96x96 windows,
five paired seeds (`42, 100, 1234, 2025, 9999`), and the split train `79,85,90,95`,
validation `81`, test `98,110` (tutorial conditions `100,103,106` excluded).  Its
reported means were:

| model | GWRMSE | interface T RMSE | interface jump MAE | mass-conservation MAE |
|---|---:|---:|---:|---:|
| T-FNO | 11.5974 | 14.5207 | 8.7655 | 0.12989 |
| U-Net | 11.5029 | 13.9057 | 8.5757 | 0.11560 |
| hybrid T-FNO | 11.6323 | 14.4567 | 8.7021 | 0.13583 |
| divergence-penalized hybrid | 11.5859 | 14.2120 | 8.6981 | 0.08669 |

These values are descriptive context only.  They are not re-used as observations in the
new pilot, and the archive checksum above is not a checksum for a future-work output.
The local compact baseline summaries are checksummed as follows:

```text
benchmark_results/multitraj96/report_summary.json
  SHA256 7cfd11a642168b2c845addf79cdfba2191664b1a4f5096ea07149753b7e58b43
benchmark_results/multitraj384_micro/native384_summary.json
  SHA256 492057863f155b49ab2d249dfdacbf6d855aa2fed8882185794cb5ce2cd8d2c6
baseline repository commit: ff5e5cc7ea924ae05be896192636506f1f1396e1
```

## Track A — extended lambda pilot

### Frozen grid and pairing

The primary extended grid is

```text
0.01, 0.03, 0.10, 0.20, 0.30, 0.45, 0.60, 0.80, 1.00
```

The optional stress points `2.00` and `5.00` may be added only if the primary grid is
complete and the run remains numerically stable.  The paired pilot seeds are
`42, 100, 1234, 2025, 9999` for every lambda, including the zero-penalty reference.
Training/validation data are used for selection; the test trajectories are untouched.
The model is the divergence-penalized local-global hybrid (`hybrid_div`).  The zero
penalty reference is the otherwise identical hybrid with `lambda_div=0`.

### Eligibility guards and reported metrics

For each candidate, report per-seed and mean validation:

* normalized data MSE;
* decoded physical spectral velocity-divergence MAE;
* interface-temperature RMSE;
* interface-temperature jump MAE;
* mass-conservation MAE on the held-out test split (reported only after selection);
* wall/dry-spot diagnostics where available.

A candidate is eligible only when both mean validation MSE and mean validation interface
temperature RMSE are no more than 1.05 times the zero-penalty reference.  Report a
deterministic 10,000-resample paired-seed bootstrap 95% interval for every mean and
candidate-minus-reference contrast.  Five seeds make these intervals pilot evidence,
not a claim of asymptotic certainty.

### Predeclared decision and stopping rules

Among eligible candidates, choose the smallest mean validation divergence.  Resolve an
exact tie toward the smaller lambda.  The following rules are frozen before inspecting
the extended results:

* **Near-optimal / retain 0.30:** no candidate outside the existing grid reduces mean
  validation divergence by at least 5% versus `0.30` while staying eligible, or the
  reduction is accompanied by more than a 5% increase in interface-temperature RMSE or
  jump MAE.
* **Continue / candidate selected:** a new candidate is eligible and reduces divergence
  by at least 5% without a greater-than-5% interface degradation.  If the selected
  candidate is the largest tested value, extend the grid before any confirmatory claim.
* **Confirmatory gate:** only after the grid is complete and the selection rule is
  satisfied may a new value be tested in a fresh 11-seed tutorial mass-conservation
  non-inferiority run and a fresh five-seed multi-trajectory replication.  Those runs
  receive new output directories and a new preregistered report.

No lambda value is called “optimal” from this pilot; at most it is a protocol-selected
operating point on the frozen grid.

## Track B — expanded cross-condition power

### Frozen held-out design

The archive contains ten wall-temperature trajectories (`79,81,85,90,95,98,100,103,106,110`).
To avoid silently converting prior tutorial conditions into training data, use rotating
five-fold condition splits.  In each fold, two trajectories are held out for testing,
two for validation, and the remaining six for training.  The folds are fixed by sorted
trajectory ID and are recorded in the run manifest before training.  No temporal window
from a held-out trajectory may appear in training.

Run all four models — vanilla T-FNO, U-Net, unpenalized hybrid T-FNO, and
divergence-penalized hybrid — with the Track-A selected lambda (or `0.30` if Track A
retains it), paired seeds `42,100,1234,2025,9999,2026,2027,2028,2029,2030,2031`.
Report fold-level and pooled paired contrasts for GWRMSE, interface T RMSE, interface
jump MAE, mass-conservation MAE, and dry-spot event metrics.  Use the same deterministic
bootstrap and exact paired sign-flip/Holm procedures as the baseline report.

The primary question is whether the U-Net reversal is consistent across held-out
conditions.  Also report heterogeneity (fold range and between-condition spread); a
pooled mean alone is insufficient evidence of a universal reversal.  Native-384
convergence is optional and is a feasibility appendix for the clearest pair only; one
epoch must never be presented as a convergence result.

## Execution ledger

| item | status at report freeze | evidence / checksum |
|---|---|---|
| Protocol and output separation | complete | this file; manuscript drafts unchanged |
| Official archive acquisition | complete on Colab T4; not extracted into the local repository | official `pool-boiling-subcooled-fc72-2d.tar.gz`, 11,108,940,120 bytes; SHA-256 `2eba140d74cbb7b01a55f0684227dea94306aea516a0f864831485d31d25f655` |
| Track-A primary grid, five seeds | not yet complete | no future-work metrics are claimed here |
| Track-B rotating five-fold, eleven seeds | not yet complete | no future-work metrics are claimed here |
| New confirmatory 11-seed run | not started | gated on Track-A selection |
| Native-384 convergence | optional / not started | prior one-epoch feasibility remains appendix-only |

The local upload bundle used to reproduce the cloud environment is
`/private/tmp/ddpinns-future-work.tar.gz` with SHA-256
`7c4f8e743b89543c7e8a009f01a42f88b2ece7abd981623cbed02731dd100154`.
This bundle contains source and tests, not the multi-gigabyte CFD archive or any
future-work checkpoint.

The archive was downloaded and hashed in the connected Colab T4 runtime, but it was not
copied into this repository.  This keeps the working tree small and avoids claiming that
the two expensive extensions were executed when their predeclared sample sizes were not
completed.  A later executor can use the checksum above to verify a fresh download before
extracting only the selected HDF5 members.

## Software validation

The canonical repository passed the focused benchmark/regression suite before this
report handoff:

```text
.venv/bin/python -m pytest -q \
  tests/test_bubbleml_benchmark.py tests/test_chf_rollout.py \
  tests/test_chf_rollout_stats.py tests/test_paper_pipeline.py
38 passed in 3.97s
```

The full repository suite is not used as a gate here because it includes preserved,
unrelated legacy tests whose optional `adaptive_dd_pinn` modules are absent in this
checkout.  No model or benchmark source code was changed for this future-work report.

## Interpretation boundary

Until the two tracks are executed to the frozen sample sizes, the only supported claim
is that the extension is specified and reproducible.  The earlier five-seed benchmark
showed a descriptive U-Net advantage over vanilla T-FNO on the four reported metrics,
while exact paired tests were not multiplicity-significant at that sample size.  This
future-work protocol is designed to test consistency and power; it does not retroactively
turn that descriptive result into a confirmatory claim.
