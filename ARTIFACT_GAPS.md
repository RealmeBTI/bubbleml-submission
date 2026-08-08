# Artifact Gaps

This file distinguishes available evidence from claims in the supplied manifest
that could not be verified in the local project.

## Missing from the assembled checkout

- Raw BubbleML HDF5 files and the 10.35 GiB legacy archive. These are intentionally
  external, but a final official download URL must be added by the author.
- The complete model checkpoint set. Four representative checkpoint hashes were
  verified; checkpoints remain external because the local set is approximately
  1.8 GiB.
- Complete per-seed configs, histories, and checkpoint provenance for the 96 x 96
  cloud cross-condition experiment. Only the compact audited summary
  `benchmark_results/multitraj96/report_summary.json` is present.
- Cross-condition field-snapshot arrays/checkpoints needed to regenerate the
  ground-truth-versus-prediction snapshot figure. A repository-wide search also
  found no compatible tutorial-split T-FNO/U-Net checkpoint pair, so the allowed
  tutorial-split fallback cannot be generated honestly. No substitute is fabricated.
- A source bibliography or citation-key mapping for every prose reference in the
  manuscript.
- A verified public GitHub repository/release and archive DOI. The author has
  supplied the intended GitHub URL and selected MIT, but the URL was not publicly
  reachable during this audit and the supplied `LICENSE` file is absent here.
- Funding confirmation and a final journal decision beyond the current
  International Journal of Heat and Mass Transfer preprint header.

## Conflicting historical records

An early `phase_history/phase1_report.md` lists a different tutorial split from the
final manuscript. This package follows the supplied final manuscript: Twall-103
train, Twall-106 validation, Twall-100 test. Historical files remain unchanged for
auditability.

## Consequence

The stored-result statistical self-test is complete and independently runnable.
A full raw-data-to-checkpoint reproduction is not yet reviewer-runnable without
the external files and links listed above.
