# Split Verification

| Protocol | Train | Validation | Test | Resolution | Direct evidence |
|---|---|---|---|---:|---|
| Tutorial | Twall-103 | Twall-106 | Twall-100 | 48×48 | manuscript Section 3.1; retained tutorial result records |
| Cross-condition | Twall-79, 85, 90, 95 | Twall-81 | Twall-98, 110 | 96×96 | `benchmark_results/multitraj96/report_summary.json` (`split`) |
| Native feasibility | NOT a convergence/ranking split | NOT REPORTED | NOT REPORTED | 384×384 | `native384_summary.json`; feasibility only |

The cross-condition summary explicitly excludes tutorial trajectories 100, 103,
and 106 and records 644/161/322 train/validation/test windows. The manuscript
now describes these protocols as distinct and does not call them equivalent.

`SPLIT_VERIFICATION = PASS`
