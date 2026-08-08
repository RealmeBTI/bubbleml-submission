# Reproducibility Status

This classification applies only to artifacts present in the local `v1.0.0`
release candidate. It does not claim public hosting or full end-to-end recovery.

| Level | Status | Evidence and boundary |
|---|---|---|
| 1. Code reproducibility | Supported | Source, documented dependencies, and tests are committed. |
| 2. Analysis reproducibility | Supported | `scripts/reproduce_reported_results.py` recomputes the stored paired statistics from committed result artifacts. |
| 3. Figure reproducibility | Partially supported | Stored-result figures and release diagrams can be regenerated; a prediction-vs-ground-truth field snapshot cannot because compatible arrays/checkpoints are absent. |
| 4. Statistical reproducibility | Supported for retained analyses | The self-test reconstructs tutorial and divergence-hybrid statistics from stored per-seed JSON. The cross-condition export is a compact summary, not complete per-seed inputs. |
| 5. Training reproducibility | Not supported from this checkout | Raw data, the full checkpoint set, and complete cross-condition per-seed exports are external or unavailable. |
| 6. Full end-to-end reproducibility | Not supported | The raw-data-to-trained-checkpoint chain cannot be executed solely from released local artifacts. |

`ARTIFACT_GAPS.md`, `DATASET.md`, and `CHECKPOINT_MANIFEST.md` are controlling
documents for the limitations above.
