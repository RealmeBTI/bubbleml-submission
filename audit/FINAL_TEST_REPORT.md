# Final Test Report

## Completed local checks

| Check | Command/result |
|---|---|
| Unit/integration suite | `MPLCONFIGDIR=/private/tmp/bubbleml-mpl python -m pytest -q` — **38 passed** in 16.15 seconds. |
| Stored-result reproduction | `python scripts/reproduce_reported_results.py --output-dir reproduced` — **PASS**; tutorial paired statistics and lambda-0.30 non-inferiority recomputed from retained artifacts. |
| Figure regeneration | After installing the already pinned `reportlab==4.4.3` dependency, `scripts/generate_submission_figures.py --output-dir submission/figures` — **PASS**; six PDF/SVG/600-DPI PNG figure families regenerated. |
| Manuscript source conversion | `scripts/build_manuscript_tex.py --pandoc pandoc` — **PASS**; generated `manuscript_elsarticle.tex` with direct citations. |
| LaTeX compilation | **NOT RUN**; no `tectonic`, `pdflatex`, `xelatex`, `lualatex`, or `latexmk` executable was available after source conversion. |

The current final release cannot claim a new successful manuscript build until an
`elsarticle`-capable TeX engine is available. Existing checked PDFs are retained
as prior artifacts but are not substituted for this build gate.
