# Final Publication Gap Matrix

| Issue | Severity | Evidence | Can repair locally? | Required human input? | Action | Verification |
|---|---|---|---|---|---|---|
| Current elsarticle PDF build unavailable | CRITICAL | No `pdflatex`, `xelatex`, `lualatex`, `latexmk`, or `tectonic` is installed; prior source conversion passes | No | Yes | Provide/install elsarticle-capable TeX and compile cleanly | No TeX errors/undefined citations; page-by-page PDF inspection |
| MIT selected but root `LICENSE` absent | HIGH | Root license search found no `LICENSE` file; metadata says MIT | No—exact supplied file is absent | Yes | Add the approved MIT LICENSE text/file | Root `LICENSE` exists and matches README/CFF/Zenodo metadata |
| GitHub release unverified | HIGH | URL is configured locally; no authenticated/public release verification exists | No | Yes | Owner pushes `v1.0.1`, creates public release | Anonymous browser shows owner/repo, README, LICENSE, tag/release |
| Zenodo archive and DOI absent | HIGH | No public record/DOI available | No | Yes | Authenticate, archive verified GitHub release, then record real DOI in a new version | DOI resolves to matching public Zenodo record |
| Full raw-data/checkpoint retraining unavailable | HIGH | `ARTIFACT_GAPS.md`, `CHECKPOINT_MANIFEST.md` | No | Yes | Supply authorized data/checkpoint/provenance links if this capability is desired | Independent raw-data-to-checkpoint execution |
| Cross-condition confirmation underpowered | MEDIUM | n=5, all primary Holm p=1.0 | No without new experiment | Yes | Run predeclared expanded protocol | New retained per-seed results and corrected analysis |
| Field snapshot unavailable | MEDIUM | No compatible field/checkpoint/data pair found | No | Yes | Supply verified compatible artifacts | Provenance-checked inference recreates figure |
| Graphical abstract | LOW | IJHMT guide describes it as encouraged, not verified mandatory | Yes, but requires author choice | Yes | Decide whether to submit optional graphical abstract | Journal portal upload check |
| Stored-result reproduction | INFORMATIONAL | Current self-test/fresh clone pass | Already repaired | No | Retain evidence boundary | 38 tests and reproduction PASS |

Publication decision: **NOT READY — HUMAN ACTION REQUIRED**.
