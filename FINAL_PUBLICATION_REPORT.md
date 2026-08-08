# Final Publication Report

## Current status

| Area | Status |
|---|---|
| Science and claim boundary | PASS within retained artifacts |
| Statistics | PASS within retained artifacts |
| Manuscript metadata and highlights | PASS |
| Current manuscript LaTeX PDF build | NOT ESTABLISHED: no elsarticle-capable TeX engine available |
| Stored-result reproduction | PASS |
| Full retraining reproduction | NOT SUPPORTED from this checkout |
| Security/public-stage scan | PASS |
| License | PENDING: author-selected MIT file is absent |
| GitHub | NOT PUBLISHED: owner authentication/authorization required |
| Zenodo | NOT PUBLISHED: requires verified GitHub release and Zenodo authentication |
| DOI | NOT VERIFIED / NOT YET AVAILABLE |

## Evidence

- The current stored-result reproduction completed with PASS; `pytest -q`
  executed 38 tests with 38 passed.
- `audit/` contains the claim, red-team, split, resolution-confound, hash,
  reproducibility, license/provenance, bibliography, security, and IJHMT
  requirement records.
- The author-designated repository is
  `https://github.com/RealmeBTI/bubbleml-submission`. It is not claimed as
  publicly verified by this report.
- The existing immutable `v1.0.0` tag remains untouched. A new release tag is
  required for the corrections recorded after it.

## Remaining human actions

1. Add the separately supplied MIT `LICENSE` file.
2. Provide an elsarticle-capable TeX installation and rerun/inspect the current
   manuscript compilation gate.
3. Publish and independently verify the GitHub repository/release under the
   owner’s authenticated account.
4. Create and verify the Zenodo archive, then insert the real DOI in a new,
   versioned release rather than altering an archived one.
5. Make any intended raw-data/checkpoint artifacts available with authorized
   source URLs and licenses if full training reproducibility is desired.
