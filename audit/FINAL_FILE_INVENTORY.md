# Final File Inventory

This inventory records scientifically material artifact groups. “GITHUB” and
“ZENODO” describe the intended release destination, not a claim that publication
has occurred. The current public-release state is pending authentication.

| Path/group | Purpose and scientific role | Intended location | Reproducibility/manuscript relevance |
|---|---|---|---|
| `manuscript/full_manuscript.md` | Controlling narrative manuscript source | GITHUB + ZENODO | Primary scientific claims and limitations |
| `manuscript/elsarticle_template.tex`, `manuscript/manuscript_elsarticle.tex`, `references.bib` | IJHMT-formatted manuscript source and references | GITHUB + ZENODO | Submission source; generated TeX is rebuildable |
| `submission/attachments/` | Cover letter, highlights, declarations, roadmap, reproducibility manifest | PRIVATE/LOCAL ONLY until submitted | Submission metadata and declarations |
| `submission/figures/` | Regenerated workflow, split, metric, and diagnostic figures | BOTH | Manuscript figures; vector and PNG forms retained |
| `submission/supplementary/` | Per-seed metric tables, statistical note, runtime record | BOTH | Supports retained-result interpretation |
| `bubbleml_benchmark/` | Dataset preparation, models, metrics, training, and evaluation code | BOTH | Enables code and pipeline inspection |
| `scripts/` | Reproduction, conversion, figure, staging, and package scripts | BOTH | Executes documented retained-result checks |
| `tests/` | Unit/integration checks | BOTH | Validates released implementation |
| `experiments/` | Retained configurations and training histories | BOTH | Partial training provenance; no full checkpoints |
| `benchmark_results/` | Retained tutorial, lambda, rollout, and compact cross-condition results | BOTH | Stored-result reproduction; cross-condition summary is compact only |
| `reproduced/` | Output of dependency-free stored-result audit | BOTH | Reproducibility evidence, regenerated on test |
| `CHECKSUMS.md`, `RELEASE_SHA256SUMS.txt`, `PACKAGE_CHECKSUMS.sha256` | Source and release integrity records | BOTH | Hash/provenance evidence |
| `audit/` | Publication, provenance, security, and scientific audits | GITHUB + ZENODO | Reviewer-facing evidence boundary |
| `output/pdf/` | Review PDFs | PRIVATE/LOCAL ONLY until submission | Readable submission artifacts; LaTeX manuscript PDF requires current TeX build |
| `output/bubbleml_submission_package.zip` | Local packaged submission snapshot | PRIVATE/LOCAL ONLY | Convenience package; regenerate from source before upload |
| `phase_history/`, `legacy/` | Historical protocol and provenance records | PRIVATE/LOCAL ONLY | Retained for audit; not final evidence unless explicitly cited |
| Raw HDF5/legacy archive and checkpoint binaries | Source data and trained weights | NOWHERE in this checkout | External/unavailable; blocks full retraining and field snapshots |
| `LICENSE` | Project code license text | NOWHERE in this checkout | MIT is author-selected but the supplied file is absent; blocks license gate |

## File-type inventory

The repository contains the required scientific source types: Markdown/TeX/Bib
manuscript sources; JSON/CSV/YAML result/configuration records; Python code and
tests; PDF/SVG/PNG figures; and no committed `.pt`, `.pth`, `.ckpt`, `.npz`, or
`.npy` checkpoint/field binary. The only generated local build auxiliaries are
ignored/ancillary and are not release evidence.

## Classification rule

No artifact is deleted solely because it is local, historical, or unavailable.
External raw data and checkpoints are explicitly declared rather than simulated
or substituted.
