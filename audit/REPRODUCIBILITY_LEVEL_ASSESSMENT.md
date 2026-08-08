# Reproducibility-Level Assessment

| Level | Status | Evidence/boundary |
|---|---|---|
| Level 1 — stored-result reproduction | Supported | `scripts/reproduce_reported_results.py` reconstructs retained tutorial and lambda statistics. |
| Level 2 — evaluation/pipeline reproduction | Partially supported | Code, tests, preprocessing/evaluation code, and compact results are present; raw data and complete cross-condition per-seed exports are not. |
| Level 3 — full retraining reproduction | Not supported | Raw data, complete checkpoints, and cross-condition training provenance are external/unavailable. |

The project must not be described as fully retrainable from this checkout.
`REPRODUCIBILITY_LEVEL_DOCUMENTED = PASS`.
