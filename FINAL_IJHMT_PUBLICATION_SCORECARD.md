# Final IJHMT Publication Scorecard

| Gate | Status | Evidence |
|---|---|---|
| Scientific claims | PASS | `audit/CLAIM_EVIDENCE_MATRIX.md`; scope corrected for resolution confound and CHF proxy |
| Statistical correctness | PASS | `audit/FINAL_STATISTICAL_VERIFICATION.md`; retained-result reproduction PASS |
| Reproducibility | BLOCKED | Stored-result reproduction PASS; raw-data/checkpoint retraining unavailable |
| Manuscript source | PASS | Markdown-to-TeX source conversion passes |
| Manuscript PDF | PASS WITH LIMITATION | Isolated 22-page TeX Live 2026 elsarticle/PDF build is clean of fatal, undefined-citation, undefined-reference, and missing-file errors; non-fatal layout/metadata warnings remain |
| Figures | PASS | Existing Fig. 1–6 audited; no phantom field snapshot |
| Tables | PASS | Retained values/splits documented in statistical and split audits |
| References | PASS | `audit/FINAL_BIBLIOGRAPHY_AUDIT.md` |
| Highlights | PASS | Five bullets, 67–77 characters |
| Author metadata | PASS | Single-author metadata audit and regenerated materials |
| License | PASS | Author-supplied root MIT `LICENSE` present; provenance audit records its SHA-256 |
| Security | PASS | Public staging scan: 0 secret and private-path hits |
| GitHub | BLOCKED | Owner publication/anonymous verification required |
| Zenodo | BLOCKED | Requires verified GitHub release and owner authentication |
| DOI | NOT VERIFIED | No archive DOI issued |
| Data availability | BLOCKED | External data/checkpoints and cross-condition provenance remain unavailable |
| Supplementary material | PASS | Retained tables, runtime, limitations, and checksums documented |
| IJHMT requirements | BLOCKED | Current guide checked; portal submission and public-release/DOI gates remain |
| Final clean clone | PASS | `audit/FINAL_FRESH_CLONE_TEST.md`: 38 tests and 550/550 checksums |

## Verdict

**NOT READY — HUMAN ACTION REQUIRED**
