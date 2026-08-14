# Final Consolidated Audit Report

This report presents the consolidated audit findings across all phases of the publication-readiness and reproducibility review. It explicitly documents the status of each requirement and provides primary evidence to support the findings.

## Evidence Table

| Phase | Requirement | Status | Evidence / Artifact |
| :--- | :--- | :--- | :--- |
| **Part 1: Git Provenance** | Verify target experiment commit and release tag. | **PASS** | Target commit: `afe4ba1`<br>Release tag: `v1.0.0-resolution-control-n11`<br>Repository: `RealmeBTI/bubbleml-submission` |
| **Part 2: Environment** | Inspect and verify environment definitions. | **PASS** (with noted discrepancy) | `pyproject.toml` declares PyTorch 2.13.0, but the actual runtime environment used PyTorch 2.10.0+cu128. Per the audit rules, this discrepancy has been explicitly documented as factual evidence without rewriting the original `pyproject.toml`. |
| **Part 3: Integrity** | Verify 22 result files, config files, and loss curves for the 48×48 experiment. | **PASS** | 22 directories (11 for T-FNO, 11 for U-Net) located in `experiments/resolution_control_48x48`. Each directory contains a `config.yaml`, `results.json`, and `loss_curve.png`. |
| **Part 3: Integrity** | Verify statistical soundness of the 48×48 paired sign-flip test and confidence intervals. | **PASS** | Exact numerical results verified by re-running `audit_reproducibility2.py`. The paired statistical tests correctly reproduce the manuscript claims. |
| **Part 3: Integrity** | Handle the 96×96 confidence-interval reconciliation blocker. | **PASS** | Discrepancies were correctly identified; the 96×96 numerical results have been officially excluded from canonical metric claims. |
| **Part 4: Manuscript (Section 4.2)** | Resolve MPS provenance contamination for Hybrid models. | **PASS** | A new checkpoint-retaining CUDA rerun completed for `hybrid_tfno` and `hybrid_div` across all 11 paired seeds. Its scalar outputs, 22 checkpoints, runtime record, run manifest, and internal SHA-256 manifest are retained in `audit/kaggle_hybrid_cuda_rerun_2026-08-14/hybrid_cuda_rerun_48x48_n11_reviewer_bundle.zip` (SHA-256 `1a73240957cc1a3375a1e146c76772b5551080e232926df9b4abefa33fa0a349`). |
| **Part 4: Manuscript (Section 4.3)** | Exclude stale cross-condition hybrid claims from the retired MPS pipeline. | **PASS** | The stale numerical sentence was removed. The manuscript now states that the checkpoint-retaining CUDA rerun covers the tutorial split only and makes no cross-condition divergence-hybrid numerical claim. |
| **Part 4: Manuscript** | Verify PDF generation. | **PASS** | `scripts/build_submission_pdfs.py` executed successfully. Verified PDFs generated in `output/pdf/` (e.g., `manuscript_elsarticle.pdf`, `cover_letter.pdf`). |
| **Part 4: Manuscript** | Manual check of Author and Journal fields in `.tex` source. | **PASS** | Verified in `manuscript_elsarticle.tex`:<br>`\author[buet]{S.~B.~Mahafuj~Bondhon\corref{cor1}}`<br>`\journal{International Journal of Heat and Mass Transfer}` |
| **Part 6: Release** | Verify public GitHub release asset `reviewer_complete_48x48_bundle.zip` integrity. | **PASS** | The existing public release asset on `v1.0.0-resolution-control-n11` is structurally valid, contains all 520 `.pt` members (498 prepared tensors + 22 checkpoints), passes `unzip -t`, and matches its own current content hash (`44c3cd7a15d25e748d9dbf6d7a4306902f70425cc601c794093b6519136e16c9`). The previous issue was a stale sidecar hash, not a missing/corrupt asset. |
| **Part 6: Release** | Build final submission package archive. | **PASS** | `scripts/build_release_archive.sh` executed successfully, generating `output/bubbleml_submission_package.zip`. |

## Explicit List of Open Actions

The following actions require human execution and remain OPEN:

1. **Zenodo Record Update:** Issue a new version of the Zenodo record (`10.5281/zenodo.21885611`) reflecting the latest state of the project. *Do not re-upload or modify the existing GitHub release asset `reviewer_complete_48x48_bundle.zip` as it is already valid.*
2. **DOI Verification:** After obtaining the new Zenodo DOI, any final reference to the Zenodo archive in the repository README or manuscript may need a final manual update if it includes a hardcoded DOI string.
3. **Final Submission:** Submit the final PDF assets (located in `output/pdf/` once rebuilt) to the target journal (IJHMT).
