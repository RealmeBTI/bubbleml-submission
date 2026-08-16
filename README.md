# BubbleML Physics-Aware Benchmark

This repository contains the BubbleML-only code and audited result artifacts for
"A Physics-Aware Benchmark for Phase-Resolved Neural Operator Learning in Boiling
Flows: Statistically Rigorous Evidence for Condition-Dependent Architecture
Trade-offs."

The central result is not that one architecture wins everywhere. On the 11-seed
tutorial split, T-FNO improves interface-temperature metrics while U-Net improves
mass conservation. On the two held-out conditions, five-seed descriptive results
favor U-Net on every primary error metric; this independent comparison is
underpowered for corrected significance. The divergence-penalized hybrid achieves
the lowest mass-conservation error in both settings, with confirmatory evidence
only on the tutorial split.

## Evidence boundaries

- Raw BubbleML HDF5 data and model checkpoints are not committed. Their recorded
  SHA-256 values are in `CHECKSUMS.md`.
- `benchmark_results/` and `experiments/` contain the machine-readable artifacts
  available locally when this package was assembled.
- The compact cross-condition export does not contain the full per-seed training
  histories or checkpoints. This gap is declared in `ARTIFACT_GAPS.md`.
- The public repository is
  `https://github.com/RealmeBTI/bubbleml-submission`. The current immutable
  `v1.1.0` release is publicly available at
  `https://github.com/RealmeBTI/bubbleml-submission/releases/tag/v1.1.0` and
  has the verified Zenodo version DOI
  `https://doi.org/10.5281/zenodo.21967986`. This DOI identifies that exact
  archived version, which includes the verified CUDA intervention reviewer bundle;
  it does not make unavailable raw data or cross-condition provenance available.
- The author-supplied root [`LICENSE`](LICENSE) is the MIT license for this
  repository's code. It does not relicense BubbleML data, checkpoints, or
  third-party dependencies.

## Recorded environment

The versions below were queried from the environment used for the final local
BubbleML work:

- Python 3.12.7
- PyTorch 2.13.0
- neuraloperator 2.0.0
- NumPy 2.5.1
- h5py 3.16.0
- Matplotlib 3.11.1
- SciPy 1.18.0
- TensorLy 0.9.0
- opt_einsum 3.4.0
- pytest 9.1.1

Create the full ML environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
pytest
```

PyTorch 2.13.0 was present in the recorded environment. If that exact build is
not available from the package index used by a reviewer, use the platform wheel
source that supplied the recorded build; no alternate version has been declared
equivalent here.

Submission-document generation has a separate lightweight dependency file:

```bash
python -m pip install -r requirements-submission.txt
python scripts/build_submission_pdfs.py --output-dir output/pdf
```

Rebuilding the Elsevier manuscript source requires Pandoc; compiling it
requires an `elsarticle`-capable TeX engine. The generated source includes a
repair for Pandoc's incompatible captionless-longtable marker. The final
pre-submission check compiled the source with TeX Live 2026, completed all
LaTeX/BibTeX passes without unresolved references or citations, and directly
inspected the resulting PDF; see `PRESUBMISSION_FINAL_CHECK.md`.

## Fast evidence self-test

This test uses only Python's standard library. It recomputes paired means and
exact sign-flip probabilities from the stored per-seed JSON, checks the archived
bootstrap intervals and Holm-adjusted values against the manuscript, and writes a
fresh SVG dry-area trace:

```bash
python scripts/reproduce_reported_results.py \
  --output-dir reproduced
```

Expected result: `PASS` and `reproduced/fig2_dry_area_trace.svg`.

## Data acquisition and preprocessing

Use only the official BubbleML release. This repository does not provide a
synthetic fallback.

```bash
python -m bubbleml_benchmark.download --help
python -m bubbleml_benchmark.prepare --help
```

The tutorial split frozen in the manuscript is Twall-103 train, Twall-106
validation, and Twall-100 test. Verify each source against `CHECKSUMS.md` before
preprocessing. For the legacy archive, use the predeclared split recorded in
`benchmark_results/multitraj96/report_summary.json`.

## Training and evaluation

Inspect the complete command-line interfaces before running an expensive job:

```bash
python -m bubbleml_benchmark.paper_train --help
python -m bubbleml_benchmark.paper_benchmark --help
python -m bubbleml_benchmark.chf_rollout --help
```

Exact per-run arguments are retained in each available
`experiments/<phase>/<model>_seed_<seed>/config.yaml`. Do not reconstruct the
cross-condition run from prose alone: its complete cloud-side per-seed export was
not supplied to this repository.

## Reproducing manuscript results and figures

| Manuscript item | Public command or evidence |
|---|---|
| Tutorial T-FNO/U-Net comparison | `python scripts/reproduce_reported_results.py --output-dir reproduced` |
| Divergence-hybrid non-inferiority | same command; source is `benchmark_results/lambda_sensitivity_030_n11/` |
| Cross-condition table | audited compact export `benchmark_results/multitraj96/report_summary.json` |
| Pareto, dry-area, lambda, loss figures | `python scripts/generate_submission_figures.py --output-dir submission/figures` |
| Full training rerun | use the recorded per-seed configs plus externally hosted source data/checkpoints |

The generated-figure script requires the pinned ML environment because it uses
Matplotlib and NumPy. `REPRODUCIBILITY_SELFTEST.md` records the clean-environment
test executed during package assembly.

## Repository map

- `bubbleml_benchmark/`: current preprocessing, models, training, evaluation,
  statistics, rollout, and plotting modules.
- `scripts/`: reviewer-facing reproduction and figure scripts.
- `legacy/`: historical one-off Phase 1 scripts retained for provenance.
- `experiments/`: available per-run configs and training histories.
- `benchmark_results/`: benchmark JSON/CSV outputs used in the manuscript.
- `phase_history/`: chronological phase reports.
- `manuscript/`: supplied Markdown and generated LaTeX source.
- `submission/`: attachments, figures, metadata, and upload package.
- `output/`: checked PDFs, consolidated ZIP, and final SHA-256 manifest.
- `tests/`: BubbleML-only tests.

## Citation and license status

The verified BubbleML bibliographic record and other identifiable references are
listed in `BIBLIOGRAPHY_VERIFICATION.md` and `manuscript/references.bib`. The
project code is licensed under the author-supplied MIT [`LICENSE`](LICENSE).

`CITATION.cff` records the supplied single-author metadata, repository URL, and
MIT license selection. Its next-version citation metadata deliberately does not
reuse the DOI of the preceding `v1.0.4` archive; that DOI is version-specific
and is recorded above and in `PRESUBMISSION_FINAL_CHECK.md`.

## Author and contact

S. B. Mahafuj Bondhon (corresponding author)\
Department of Mechanical Engineering\
Bangladesh University of Engineering and Technology (BUET)\
Ramna, Dhaka-1000, Bangladesh\
ORCID: 0009-0009-6695-365X\
Email: 2210062@me.buet.ac.bd\
Secondary email: sbmahafujbondhon@gmail.com\
Phone: +880 1865375578

## Release status and limitations

The immutable `v1.0.4` release and corresponding Zenodo archive are verified
above. Existing tags remain immutable. This working version contains
post-`v1.0.4` manuscript and metadata corrections, so it requires its own
release/archive before it can inherit a version-specific DOI. Historical audit
files retain their original status and are not silently rewritten.

`REPRODUCIBILITY_STATUS.md` classifies the supported levels precisely: stored
analysis and the checked figures can be reproduced from the committed artifacts;
full training and end-to-end reproduction cannot be performed from this checkout
alone. `DATASET.md` and `CHECKPOINT_MANIFEST.md` distinguish external source
artifacts from committed evidence.
