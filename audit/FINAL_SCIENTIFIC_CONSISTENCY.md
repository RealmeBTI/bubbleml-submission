# Final Scientific Consistency Audit

## Scope

Searched manuscript/source, results JSON/CSV, experiment YAML/JSON, generated
figures, and phase reports for split names, sample sizes, lambda, bounded alpha,
interface/conservation, dry-area/CHF, FNO/U-Net, and BubbleML terms.

## Reconciled findings

| Topic | Final consistent statement | Source of record |
|---|---|---|
| Tutorial split | Twall-103 train, Twall-106 validation, Twall-100 test; n=11 for T-FNO/U-Net test | manuscript Section 3.1; retained result artifacts |
| Cross-condition split | 79/85/90/95 train, 81 validation, 98/110 independent test; n=5 | `multitraj96/report_summary.json` |
| Tutorial architecture comparison | T-FNO improves interface-temperature metrics; U-Net improves mass conservation; no overall GWRMSE winner | stored self-test and manuscript Section 4.1 |
| Cross-condition comparison | U-Net descriptively leads T-FNO on all four primary error metrics; no Holm-confirmed claim at n=5 | `multitraj96/report_summary.json` |
| Divergence penalty | Lambda 0.30 is the upper tested eligible value, not an interior optimum; tutorial mass non-inferiority passes | `lambda_sensitivity_030_n11/` |
| Bounded alpha | Alpha is constrained to [0,1]; it does not establish an architecture winner | Phase 5 artifacts/manuscript Section 4.2 |
| Dry-area/CHF | No sustained event in available trajectories; no validated CHF-detection claim | rollout result artifacts/manuscript Section 4.5 |
| Field snapshot | Unavailable and not used as evidence | `ARTIFACT_GAPS.md` |

Historical phase notes contain superseded pilot outcomes and paths. They are
retained outside the filtered public staging tree for auditability and are not
used to support final claims. No unexplained contradiction remains in the final
manuscript/result evidence boundary.
