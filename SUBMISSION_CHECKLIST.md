# Submission Checklist

Status definitions: **ready** means mechanically complete from available evidence;
**needs human input** means an author-only fact or action is missing; **needs
verification** means the required source artifact was not supplied.

## Upload documents

| File | Purpose | Status |
|---|---|---|
| `output/pdf/manuscript_elsarticle.pdf` | Elsevier-format manuscript proof | **needs human input** — author/journal fields; **needs verification** — unresolved citations |
| `output/pdf/cover_letter.pdf` | Cover letter | **needs human input** — all supplied bracketed fields retained |
| `output/pdf/highlights.pdf` | Submission highlights | **ready**, subject to author approval |
| `output/pdf/author_statements_and_coi.pdf` | Author, CRediT, funding, COI, data statements | **needs human input** — supplied bracketed fields retained |
| `output/pdf/reproducibility_manifest.pdf` | Standalone reproducibility manifest | **needs human input** — public URLs/DOI |
| `output/pdf/submission_roadmap.pdf` | Author-side submission roadmap | **ready** as guidance; normally not uploaded to a journal |
| `output/pdf/supplementary_material.pdf` | Methods/evidence supplement | **ready** for available evidence; external artifacts still required for full rerun |

## Figures

| Files | Purpose | Status |
|---|---|---|
| `submission/figures/fig1_pareto_front.{pdf,svg,png}` | Interface/conservation trade-off | **ready** |
| `submission/figures/fig2_dry_area_trace.{pdf,svg,png}` | Dry-area rollout trace | **ready** |
| `submission/figures/fig3_lambda_sensitivity.{pdf,svg,png}` | Divergence-lambda sensitivity | **ready** |
| `submission/figures/fig4_loss_curves.{pdf,svg,png}` | Available training histories | **ready** |
| Ground-truth/prediction field snapshots | Qualitative cross-condition comparison | **needs verification** — source arrays/checkpoints unavailable |

## Sources and reproducibility evidence

| File/directory | Purpose | Status |
|---|---|---|
| `manuscript/full_manuscript.md` | Supplied canonical manuscript source | **ready**; SHA-256 `40c9d1ece71dae77b5251ca91f4525c7b8a4fa711717a2fff9ea19ca67b02f4d` |
| `manuscript/manuscript_elsarticle.tex` and `references.bib` | Editable journal source | **needs human input/verification** as above |
| `submission/attachments/*.md` | Supplied editable attachments | **ready**, byte-identical to supplied files |
| `bubbleml_benchmark/`, `scripts/`, `tests/` | Pipeline, analysis, plotting, tests | **ready** |
| `experiments/`, `benchmark_results/` | Available machine-readable configurations/results | **ready** for archived analyses; incomplete for full cross-condition rerun |
| `submission/supplementary/*.csv` | Per-seed primary metrics and lambda summary | **ready** |
| `REPRODUCIBILITY_SELFTEST.md` | Clean-clone reviewer test record | **ready** after recorded PASS |
| `CHECKSUMS.md` | Source/archive/checkpoint integrity values | **needs human input** for three historically unassigned hashes |
| `BIBLIOGRAPHY_VERIFICATION.md` | Primary-record citation audit | **needs human input** for unresolved prose citations |
| `ARTIFACT_GAPS.md` | Explicit missing-artifact declaration | **ready** |

## Attachment-source identity

| Supplied source retained as | SHA-256 |
|---|---|
| `submission/attachments/author_statements_and_coi.md` | `55b2a48e97b8d8f0ac0f21fd9a204fb733764db3ab82579e9d145274e11c1f8e` |
| `submission/attachments/cover_letter.md` | `bbf39c6f7cbea121300c7b55da5b165feb0a351a7a34ecdc55ec8ddd2f51f6c3` |
| `submission/attachments/highlights.md` | `f062a296f5f79fb9eb897f1145b3aad0472f24c93d8aefb3bf62a2976bc83517` |
| `submission/attachments/reproducibility_manifest.md` | `f896e59a99795ed94be52bfe6e436f59147e2e903aaa1f42b0624996f9e91a6d` |
| `submission/attachments/submission_roadmap.md` | `7eb9833e4a0e46527ec7d2e7c1338b817ecb42891a3dedfa50719a0e0c25f9f2` |

## Release/archive files

| File | Purpose | Status |
|---|---|---|
| `submission/RELEASE_NOTES_v1.0-submission-draft.md` | GitHub release draft | **ready**, subject to author approval |
| `submission/zenodo_metadata_draft.json` | Zenodo metadata draft | **needs human input** — creators, license, URL/DOI |
| Local tag `v1.0-submission-draft` | Reproducible local release point | **ready** |
| Public GitHub release and Zenodo record | Public archival | **needs human input** — account access and publication action |
| `output/bubbleml_submission_package.zip` | Consolidated upload/review archive | **ready** after final checksum generation |

The portal upload and submission click remain human actions.
