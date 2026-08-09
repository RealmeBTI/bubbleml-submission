# Final Pre-Submission Check

Audit date: 2026-08-09. This is new final-state evidence; it does not overwrite historical audit files or their earlier publication statuses.

## Status vocabulary

- **PASS** — directly checked during this audit.
- **BLOCKED** — a required capability or artifact is absent.
- **NOT VERIFIED** — no adequate direct evidence was obtained.
- **LIMITATION** — a scientific scope boundary, not a publication-status claim.

## Repository and public infrastructure

| Gate | Status | Evidence |
|---|---|---|
| Audit baseline | PASS | At audit start: branch `main`; commit `0bb5581d8d645a30e53c99cb042a5a5e303df740`; tag `v1.0.4`; clean tracked state. |
| Public GitHub repository | PASS | Anonymous GitHub API returned `RealmeBTI/bubbleml-submission`, `private=false`, default branch `main`, and MIT license metadata. |
| Public GitHub release | PASS | Anonymous API returned [v1.0.4](https://github.com/RealmeBTI/bubbleml-submission/releases/tag/v1.0.4), published 2026-08-09. |
| Public tag | PASS | Anonymous GitHub API returned annotated tag object `1a563d7c2d7b49594f4e46526668e382087db6ed` for `v1.0.4`. |
| DOI resolution | PASS | `https://doi.org/10.5281/zenodo.21858198` redirected to [Zenodo record 21858198](https://zenodo.org/records/21858198); the public API returned HTTP 200. |
| Zenodo identity | PASS | Record 21858198 is *BubbleML Physics-Aware Benchmark*, version `v1.0.4`, published 2026-08-09; creator Bondhon, S. B. Mahafuj; ORCID `0009-0009-6695-365X`; MIT license; matching repository/tag URL. |
| Zenodo archive file | PASS | Downloaded `RealmeBTI/bubbleml-submission-v1.0.4.zip` MD5 `2c8f259f84a50697e56d315f36e23ae6` matches the public record. |
| Archive/version consistency | PASS | Archive root commit `1a563d7` contains the public `v1.0.4` source snapshot, `LICENSE`, `README.md`, `CITATION.cff`, and listed manuscript files. |
| Corrected-worktree DOI | BLOCKED | The verified DOI is specific to immutable `v1.0.4`. This worktree has post-archive manuscript, figure-reference, and metadata corrections and needs a new archive before it can cite a current-version DOI. |

## Manuscript PDF

| Gate | Status | Evidence |
|---|---|---|
| Clean LaTeX build | PASS | TeX Live 2026 `latexmk` completed all LaTeX/BibTeX passes; final log had no undefined references, undefined citations, missing files, or fatal errors. |
| Current PDF | PASS | `manuscript/manuscript_elsarticle.pdf` was replaced with the clean 26-page output, SHA-256 `e8c309e0702f02446cb70f4d860e7c817961f6e77fff994bbe6ea8bbabce5754`. |
| Direct PDF inspection | PASS | Rendered/inspected title and author page, DOI notice page, Sections 4.4–4.6, all limitations-table pages, and final references page. No blank pages, clipping, broken symbols, or missing figures observed. |
| Section 4.4 integrity | PASS | Rendered result includes all four models, metrics, paired differences, confidence intervals, exact p=.0625, Holm p=1.0, and complete continuation discussion. |
| Section 5.5 limitations | PASS | The 10 intended dimensions render continuously across three pages. |
| Figure rendering/cross-references | PASS | Six vector-PDF figures render with captions. The generator now creates explicit labels for Pareto, split design, workflow, lambda sensitivity, dry-area traces, and training histories; text references resolve through those labels. |
| Tables, equations, references | PASS | Direct rendered inspection showed them present; final build log contains no unresolved citations or references. Non-fatal TeX box/PDF-metadata warnings remain cosmetic. |

## Scientific evidence and reproducibility

| Gate | Status | Evidence |
|---|---|---|
| Stored-result reproduction | PASS | `python3 scripts/reproduce_reported_results.py --output-dir reproduced_final` returned `PASS`; tutorial means, intervals, exact p-values, Holm values, and divergence-hybrid comparison match stored-result output. |
| Statistical audit | PASS | Historical `audit/FINAL_STATISTICAL_VERIFICATION.md` retains its documented 38-test scope; a fresh full suite also passed in this audit. |
| Full pytest suite | PASS | After approved installation of pinned `neuraloperator==2.0.0` into the existing project virtual environment, `../.venv/bin/python -m pytest -q -rA` completed with **38 passed in 15.55s**. |
| Raw-data-to-checkpoint retraining | BLOCKED | Raw BubbleML files, complete checkpoint set, and complete cross-condition per-seed provenance are not present. |
| Cross-condition inference | LIMITATION | Two held-out conditions and five paired seeds are descriptive/underpowered; no Holm-significant cross-condition ranking is claimed. |
| Field snapshots | BLOCKED | Compatible prediction arrays/checkpoints are unavailable. No synthetic, reconstructed, or illustrative inference figure was created. |
| CHF claim | LIMITATION | No verified stable-to-CHF transition or synchronized wall-heat-flux series exists; the dry-area signal remains proxy-only. |
| Divergence-penalty selection | LIMITATION | `lambda_div=.30` is the tested upper boundary; behavior beyond it remains untested. |

## Metadata and licensing

| Gate | Status | Evidence |
|---|---|---|
| Author metadata | PASS | Manuscript, cover letter, author statements, `CITATION.cff`, local metadata, and live Zenodo record agree on author, BUET affiliation, ORCID, and corresponding email. |
| CRediT/COI/funding/data statement | PASS | Present in `submission/attachments/author_statements_and_coi.md`; Data Availability now names the verified predecessor release and scope. |
| Root LICENSE | PASS | `LICENSE` exists; SHA-256 `101850044a7242f47440323a3ae67dce5eb2b53b16ea1e78d5ff39fda4709dec`; GitHub API and Zenodo metadata identify MIT. |
| External approved-license comparison | NOT VERIFIED | No separate approved-license source file or reference hash was supplied for byte-for-byte comparison. |
| Citation/Zenodo metadata | PASS | Next-version metadata is `1.0.5`; it does not reuse the version-specific `v1.0.4` DOI. Local metadata records the verified predecessor separately. |

## Artifacts and staging

| Gate | Status | Evidence |
|---|---|---|
| Manuscript source/PDF/bibliography/figures | PASS | Present; public-staging script now includes `manuscript_elsarticle.pdf`. |
| Submission attachments | PASS | Cover letter, highlights, author statements, and reproducibility manifest are present. |
| Historic audit preservation | PASS | No historical audit report was rewritten to make a prior state appear resolved. |
| Public staging build | PASS | `python3 scripts/prepare_public_release.py --output-dir /private/tmp/bubbleml-public-stage` produced the filtered tree. All staged manifest entries verified with `shasum -a 256 -c RELEASE_SHA256SUMS.txt`. |
| Private-path and narrow secret check | PASS | The staged public text contains no `/Users`, `/home`, `/private`, `/tmp`, or `/var` path; no `.env`, PEM, or `id_rsa` filename was staged. This is not a substitute for a full credential scanner. |

## Release decision

The public `v1.0.4` release and [Zenodo DOI 10.5281/zenodo.21858198](https://doi.org/10.5281/zenodo.21858198) are verified and correctly identify that immutable archive. The corrected worktree is not entitled to that DOI.

The stored-result check and 38-test suite pass in the repaired environment. Full raw-data-to-checkpoint retraining remains blocked by the explicitly unavailable artifacts. A new immutable GitHub/Zenodo release is still required before this corrected worktree can receive and cite its own DOI. Peer-review outcome remains uncertain.
