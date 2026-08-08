# IJHMT Red-Team Review

| Severity | File/section | Problem and evidence | Scientific consequence | Correction / computation needed |
|---|---|---|---|---|
| CRITICAL (resolved) | Manuscript Introduction, Contributions, Discussion | The two protocols differed in spatial resolution as well as trajectory conditions. | A wall-temperature causal interpretation would be invalid. | Rewrote causal language; no new computation can isolate the factor retrospectively. |
| CRITICAL (open) | Section 7; `ARTIFACT_GAPS.md` | Raw data, complete checkpoints, and per-seed cross-condition exports are unavailable. | Full training and field-level replication cannot be claimed. | Keep boundaries explicit; new data/checkpoint release required. |
| MAJOR (open) | Section 4.4 | Cross-condition n=5 has minimum two-sided exact p=.0625 and Holm p=1.0. | No confirmatory architecture ranking is established there. | Retain descriptive language; a larger predeclared study is required. |
| MAJOR (open) | Manuscript PDF build | No elsarticle-capable TeX engine is installed. | A current clean manuscript PDF build cannot be certified. | Install/provide compatible TeX, compile, inspect log/PDF. |
| MODERATE (resolved) | Introduction/CHF framing | Earlier prose risked conflating dry-area diagnostics with CHF detection. | Could overstate physical validity. | Replaced with proxy-only framing. |
| MODERATE (open) | License/release | MIT is selected but the actual `LICENSE` file is absent; remote release unavailable. | Public-release/legal gate remains incomplete. | Add supplied file, publish/verify release under owner authentication. |
| MINOR (open) | Journal submission package | Graphical abstract is encouraged by current guide; final journal portal checks remain required. | Submission completeness risk. | Author decides whether to provide one. |

## Overall reviewer disposition

The retained tutorial statistical evidence and its stated limitations are
defensible. The submission is **not ready** for a final IJHMT upload because
the TeX build, license file, and public/archive release gates remain open.
`RED_TEAM = PASS` as an audit, not as a finding of publication readiness.
