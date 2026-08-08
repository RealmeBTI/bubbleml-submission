# Phase 2 Upstream Handoff Audit

## Baseline

- `PHASE1_FINAL_COMMIT=db21b9412364a6bfb7c9ccae2a50cf76dd3dff0c`
- Phase 2 starting HEAD: `db21b9412364a6bfb7c9ccae2a50cf76dd3dff0c`
- Existing tag: `v1.0-submission-draft` at `6f03d5df7a54a56a890a94ece740a1bd56dd7b4e`.
- Safety checkpoint: annotated tag `phase2-baseline-db21b94` resolves to the
  Phase 1 commit above.
- No Git remotes were configured at handoff.

## Phase 1 changes independently inspected

Commit `db21b94` added the workflow and split diagrams, updated the manuscript
and bibliography, refreshed the checked submission PDFs/archive, and amended
artifact-gap and checksum records. Its changed-file list contains no deleted
tracked file. The working tree also held a whitespace-only user edit to
`REMAINING_HUMAN_ACTIONS.md` and untracked macOS/build/extracted-package files;
none was discarded or included in the Phase 2 release commit.

## Re-audit result

- Bibliographic records: the five requested records are represented in
  `manuscript/references.bib`; the current arXiv records confirm the Dunlap,
  LOGLO-FNO, and Project-and-Generate titles/authors. The Ravichandran DOI and
  publisher metadata are documented in `BIBLIOGRAPHY_VERIFICATION.md`.
- Historical hashes: `7cfd11…e58b43` matches
  `benchmark_results/multitraj96/report_summary.json`; `492057…d8d2c6` matches
  `benchmark_results/multitraj384_micro/native384_summary.json`; and
  `7c4f8e…100154` remains unassigned because its temporary upload bundle is
  absent. No provenance was invented.
- Field snapshot: no compatible cross-condition arrays/checkpoints exist, and
  no compatible tutorial T-FNO/U-Net checkpoint pair was found. No snapshot is
  represented as evidence.
- Figures: workflow and split diagrams accurately state the documented stages,
  tutorial split, and cross-condition split.

## Unresolved inherited items

Raw data, complete checkpoints, complete cross-condition per-seed exports,
author metadata, license, public repository URL, Zenodo record, and DOI remain
unavailable. `ARTIFACT_GAPS.md` and `REMAINING_HUMAN_ACTIONS.md` retain those
limitations.
