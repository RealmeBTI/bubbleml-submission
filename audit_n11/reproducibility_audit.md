# Reproducibility Audit — n=11 Resolution-Control Integration

## Audit Date: 2026-08-10
## Auditor: Agent (automated + manual verification)

---

## Tutorial 48x48 Split (Primary Backbone)

| Factor | Status | Notes |
|---|---|---|
| Random seeds (7,17,42,100,314,1234,2025,2718,4242,7777,9999) | VERIFIED | Stored in benchmark_results.json metadata |
| n=11 | VERIFIED | 11 paired seeds confirmed in raw_seed_metrics |
| Dataset identity (Twall-103/106/100) | VERIFIED | SHA-256 in CHECKSUMS.md and manuscript Table |
| Temporal range (timesteps 30-198, 169 frames) | VERIFIED | Documented in §3.1 |
| Train/val/test roles | VERIFIED | Frozen before any model training |
| Model configuration | VERIFIED | Per-seed config.yaml in experiments/resolution_control_96x96/ |
| Statistical method | VERIFIED | reproduce_reported_results.py PASS |
| Numerical self-test | VERIFIED | python scripts/reproduce_reported_results.py — output: PASS |
| Bootstrap CI | VERIFIED | 10,000-sample paired bootstrap |
| Holm-Bonferroni | VERIFIED | 4-metric family; correct implementation |
| Hardware | KNOWN-DIFFERENCE | Apple M2 / MPS (not cross-validated with CUDA) |
| Checkpoints | AVAILABLE | Phase 1 tutorial checkpoints committed |
| Python/PyTorch version | RECORDED | Python 3.12.7, PyTorch 2.13.0 |
| Full end-to-end retraining | NOT AVAILABLE | Raw HDF5 data not committed |

## Cross-Condition 96x96 Multi-Trajectory (n=5)

| Factor | Status | Notes |
|---|---|---|
| Random seeds (42,100,1234,2025,9999) | RECORDED | In report_summary.json |
| n=5 | VERIFIED | Underpowered; all Holm=1.0 |
| Dataset identity (Twall 98, 110) | RECORDED | SHA-256 of legacy archive in §3.1 |
| Full per-seed results | NOT AVAILABLE | Compact summary only |
| Checkpoints | NOT COMMITTED | Cloud-side only |
| Statistical method | VERIFIED | Same audited implementation |
| Reproducibility level | LEVEL 1 | Reproducible from stored compact summary |

## Exploratory 96x96 Tutorial-Split (n=11) — NEW

| Factor | Status | Notes |
|---|---|---|
| Random seeds (all 11) | VERIFIED | Stored in benchmark_results.json metadata |
| n=11 | VERIFIED | 11 paired seeds in raw_seed_metrics |
| Dataset trajectories | VERIFIED (nominal) | Same Twall-103/106/100 as tutorial |
| Raw HDF5 checksums for 96x96 processing | NOT RETAINED | Gap documented in control_matrix.md |
| Temporal range (30-195, 166 samples) | VERIFIED | Differs from 48x48 (30-198, 169 frames) |
| Per-seed config.yaml | COMMITTED | experiments/resolution_control_96x96/tfno_seed_*/config.yaml |
| Per-seed results.json | COMMITTED | experiments/resolution_control_96x96/ |
| Merged benchmark_results.json | COMMITTED | benchmark_results/resolution_control_96x96/ |
| Statistical analysis | VERIFIED | resolution_control_analysis.json; numbers recomputed in audit |
| Paired differences (n=11 GWRMSE) | VERIFIED | +0.10868116 (matches audit recomputation) |
| Holm-adjusted p-values | VERIFIED | Matches resolution_control_analysis.json |
| Checkpoints | NOT COMMITTED | Kaggle-resident; not in authorized artifact set |
| Source commit | RECORDED | eb7884e (experiment/resolution-control-n11) |
| Hardware | KNOWN-DIFFERENCE | NVIDIA Tesla T4 / CUDA (differs from 48x48 MPS) |
| Reproducibility level | LEVEL 1 | Analysis reproducible from committed JSON; training not reproducible without external environment |

---

## Reproducibility Classification Used in Manuscript

- LEVEL 0: Claim only, no artifact
- LEVEL 1: Reproducible from stored aggregate metrics/JSON
- LEVEL 2: Reproducible from stored per-seed results + scripts (but not checkpoints)
- LEVEL 3: Reproducible from checkpoints + stored scripts (no raw data needed)
- LEVEL 4: Fully end-to-end reproducible from raw data

Tutorial backbone: LEVEL 2-3 (per-seed JSONs + some checkpoints available)
Cross-condition: LEVEL 1 (compact summary only)
96x96 exploratory: LEVEL 1 (per-seed JSONs; checkpoints absent)

## Conclusion

The manuscript correctly uses "reproducible from retained aggregate metrics"
language for cross-condition and exploratory results, and does not claim
"fully end-to-end reproducible" for any of these.

STATUS: REPRODUCIBILITY AUDIT PASS (within stated artifact boundaries)
