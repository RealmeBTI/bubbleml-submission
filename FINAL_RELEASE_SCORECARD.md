# Final Release Scorecard

| Gate | Status | Basis |
|---|---|---|
| Scientific integrity | PASS | Final claims retain the tutorial/cross-condition distinction and artifact boundaries. |
| Citation integrity | PASS | Requested verified records are in the bibliography and directly cited in regenerated LaTeX. |
| Hash integrity | PASS WITH DECLARED GAP | Two historical hashes match local artifacts; the third remains explicitly unassigned. |
| Artifact provenance | PASS WITH DECLARED GAPS | Available and unavailable artifacts are distinguished without substitution. |
| Numerical consistency | PASS | Final table numbers match machine-readable summaries and self-test results. |
| Statistical reproducibility | PASS FOR RETAINED ANALYSES | Stored tutorial and lambda-0.30 analyses reproduce; full cross-condition per-seed export is absent. |
| Software tests | PASS | `pytest -q`: 38 passed. |
| Manuscript build | FAIL | The TeX engine was unavailable in the audited environment after source regeneration. |
| Figure QA | PASS | Six figure families verified; snapshot not claimed because inputs are absent. |
| Security scan | PASS | High-confidence key/token/password/auth-header scan found no secrets in filtered public staging. |
| Private-path scan | PASS | Filtered public staging had no `/Users/`, `/home/`, `/private/`, `/tmp/`, `/var/`, Windows-drive, or local-username paths after documented redaction. |
| Checksum verification | PASS | Every file in filtered public staging passed `shasum -a 256 -c RELEASE_SHA256SUMS.txt`. |
| Git integrity | PENDING | Final commit and v1.0.0 tag not yet created. |
| Local fresh-clone test | PENDING | Runs after final commit/tag. |
| Public GitHub clone test | N/A | No authenticated public GitHub release. |
| GitHub publication | NOT PUBLISHED | No configured remote or verified authentication. |
| Zenodo publication | NOT PUBLISHED | No verified creator metadata, license, authentication, or deposition. |
| DOI verification | N/A | No DOI exists. |

## Final status

**HUMAN INPUT REQUIRED.** It cannot be promoted to READY while the manuscript
build environment, license/creator metadata, and public-hosting/archive gates
remain unresolved.
