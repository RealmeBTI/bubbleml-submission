# Final IJHMT Publication Status

## Decision

`BLOCKED` for external publication and IJHMT portal submission. The corrected
local release target is `v1.0.3`; it supersedes, but does not alter, the
immutable locally audited `v1.0.2` tag (`c60a817fb01c324ebd5509a0ca3b586cb830c5f0`).

## Evidence-based gates

| Gate | Status | Evidence and boundary |
|---|---|---|
| Repository baseline | PASS | `v1.0.2` resolves to `c60a817fb01c324ebd5509a0ca3b586cb830c5f0`; prior tags were not moved. |
| Project license | PASS | Author-supplied root `LICENSE` contains MIT text; SHA-256 `101850044a7242f47440323a3ae67dce5eb2b53b16ea1e78d5ff39fda4709dec`. |
| Manuscript source | PASS | `scripts/build_manuscript_tex.py --pandoc pandoc` regenerates `manuscript/manuscript_elsarticle.tex`; invalid Pandoc longtable marker and Unicode minus/multiplication failures were repaired. |
| Manuscript PDF | PASS WITH LIMITATION | Isolated TeX Live 2026 `latexmk`/BibTeX build completed: 22 pages, SHA-256 `558d57140016a2faabc6594987e4e70dd253c7b9da84ed83dd6598fad36881f9`; final log has no fatal errors, missing files, undefined citations, or undefined references. Non-fatal hyperref and box-layout warnings remain. |
| Manuscript visual QA | PASS WITH LIMITATION | All 22 pages were rendered and checked as a contact sheet; pages 1, 6, 12, and 22 received high-resolution inspection. This local check does not substitute for a journal production proof. |
| Stored-result reproduction | PASS | `scripts/reproduce_reported_results.py --output-dir reproduced` returned `PASS` on 2026-08-09; the full test suite returned `38 passed`. The project supports stored-result reproduction. |
| Full raw-data/checkpoint retraining | BLOCKED | Authorized raw data, complete checkpoints, and complete cloud-side cross-condition exports are not retained in this checkout. |
| Primary scientific interpretation | PASS WITH LIMITATION | The repository supports its retained-result, condition-dependent trade-off interpretation. It does not establish a universal model ranking; the independent cross-condition test is underpowered as documented in the manuscript and audits. |
| GitHub publication | BLOCKED | `gh auth status` reports the configured `RealmeBTI` token invalid; no anonymous public release verification was obtained. `GITHUB_AUTH_REQUIRED`. |
| Zenodo archive / DOI | NOT VERIFIED | No verified public GitHub release or Zenodo record is available. No DOI is asserted. |
| IJHMT submission portal | NOT VERIFIED | No authorized portal upload or final editorial file check was performed. |

## Verification record

- The corrected manuscript PDF is the tracked review artifact at
  `output/pdf/manuscript_elsarticle.pdf`. The untracked working-directory PDF
  under `manuscript/` is excluded from the release archive to prevent a stale
  local build artifact being packaged.
- `scripts/build_release_archive.sh` excludes transient `manuscript/*.pdf` and
  `manuscript/*.spl` files; the verified review PDF is included from
  `output/pdf/`.
- Package checksums and the public-release staging manifest must be regenerated
  after the final archive is built, then verified before any publish attempt.
- For this release target, the regenerated public stage verified 554/554
  SHA-256 entries and the filtered security/path scan found no credential-like
  assignments, private keys, or absolute local paths. The 26-entry package
  checksum file is also verified after its final archive hash is recorded.

## Required authorized actions

1. Authenticate the GitHub CLI as `RealmeBTI`, push `main` and the new annotated
   `v1.0.3` tag, create the public release, and verify it anonymously.
2. Enable Zenodo's GitHub integration, archive that verified public release, and
   record only the resolving DOI in a subsequent versioned update.
3. Complete the IJHMT portal workflow and respond to any template-specific
   editorial requirements. Do not represent this repository as submitted until
   that action is independently verifiable.
