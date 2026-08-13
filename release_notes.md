This release formally archives the completed 48x48 tutorial-split T-FNO vs U-Net resolution-control experiment with n=11 seeds per model.

## Environment Discrepancy Observation
During the final audit, we noted an inconsistency regarding the PyTorch version:
- The declared environment dependency (`requirements.txt` / project setup) pins **PyTorch 2.13.0**.
- The hardware/runtime record observed during Kaggle execution recorded **PyTorch 2.10.0+cu128**.

We treat the execution log (`2.10.0+cu128`) as factual evidence of the runtime. The discrepancy is explicitly documented here for reviewers.

## Artifacts
The attached `reviewer_complete_48x48_bundle.zip` contains:
- The prepared dataset manifest and binary tensor splits.
- All 22 checkpoint files (.pt).
- Raw execution and submission logs.

A SHA-256 digest is attached to ensure archive integrity.
