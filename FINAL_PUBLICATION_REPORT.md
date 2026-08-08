# Final Publication Report

## Current status

| Area | Status |
|---|---|
| Science and claim boundary | PASS within retained artifacts |
| Statistics | PASS within retained artifacts |
| Manuscript metadata and highlights | PASS |
| Current manuscript LaTeX PDF build | PASS WITH LIMITATION: isolated 22-page elsarticle/PDF build completed; non-fatal layout/metadata warnings remain |
| Stored-result reproduction | PASS |
| Full retraining reproduction | NOT SUPPORTED from this checkout |
| Security/public-stage scan | PASS |
| License | PASS: author-supplied root MIT `LICENSE` is present |
| GitHub | NOT PUBLISHED: owner authentication/authorization required |
| Zenodo | NOT PUBLISHED: requires verified GitHub release and Zenodo authentication |
| DOI | NOT VERIFIED / NOT YET AVAILABLE |

## Evidence

- The current stored-result reproduction completed with PASS; `pytest -q`
  executed 38 tests with 38 passed. A fresh clone of the audited source/package
  commit repeated both checks and verified 550/550 public-stage manifest entries.
- `audit/` contains the claim, red-team, split, resolution-confound, hash,
  reproducibility, license/provenance, bibliography, security, and IJHMT
  requirement records.
- The author-designated repository is
  `https://github.com/RealmeBTI/bubbleml-submission`. It is not claimed as
  publicly verified by this report.
- The existing immutable `v1.0.0`, `v1.0.1`, and `v1.0.2` tags remain
  untouched. The post-`v1.0.2` corrections are released only under a new
  `v1.0.3` tag.

## Remaining human actions

1. Provide an elsarticle-capable TeX installation and rerun/inspect the current
   manuscript compilation gate.
2. Publish and independently verify the GitHub repository/release under the
   owner’s authenticated account.
3. Create and verify the Zenodo archive, then insert the real DOI in a new,
   versioned release rather than altering an archived one.
4. Make any intended raw-data/checkpoint artifacts available with authorized
   source URLs and licenses if full training reproducibility is desired.
