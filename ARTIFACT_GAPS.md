# Artifact Gaps

This file distinguishes available evidence from claims in the supplied manifest
that could not be verified in the local project.

## Missing from the assembled checkout

- Raw BubbleML HDF5 files and the 10.35 GiB legacy archive. These are intentionally
  external, but a final official download URL must be added by the author.
- The complete 96 x 96 cross-condition checkpoint set remains unavailable.
  For the canonical 48 x 48 tutorial split, all 22 baseline checkpoints and all
  22 newly rerun intervention checkpoints are retained in checksum-verified
  reviewer bundles.
- Complete per-seed configs, histories, and checkpoint provenance for the 96 x 96
  cloud cross-condition experiment. Only the compact audited summary
  `benchmark_results/multitraj96/report_summary.json` is present.
- Cross-condition field-snapshot arrays/checkpoints needed to regenerate a
  cross-condition ground-truth-versus-prediction snapshot figure. Compatible
  tutorial-split tensors and checkpoints are now locally retained, but no new
  snapshot figure is claimed until it is generated directly from those artifacts.
- A source bibliography or citation-key mapping for every prose reference in the
  manuscript.
- A public immutable archive containing the newly recovered CUDA intervention
  bundle. This pass intentionally does not push, tag, alter an existing release,
  or create a Zenodo version; release approval remains separate.

## Conflicting historical records

An early `phase_history/phase1_report.md` lists a different tutorial split from the
final manuscript. This package follows the supplied final manuscript: Twall-103
train, Twall-106 validation, Twall-100 test. Historical files remain unchanged for
auditability.

## Consequence

The canonical tutorial and CUDA intervention stored-result self-tests are complete
and independently runnable from locally retained artifacts. A full raw-HDF5-to-
checkpoint reproduction and the cross-condition checkpoint-level reproduction
still require the external files listed above.
