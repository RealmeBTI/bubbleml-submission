# Resolution-Confound Audit

## Verified designs

| Protocol | Spatial resolution | Trajectories | Evidence |
|---|---:|---|---|
| Tutorial | 48×48 | train 103, validation 106, test 100 | `manuscript/full_manuscript.md`, tutorial result files |
| Cross-condition | 96×96 | train 79/85/90/95, validation 81, test 98/110 | `benchmark_results/multitraj96/report_summary.json` |
| Native feasibility | 384×384 | legacy-archive feasibility check | `benchmark_results/multitraj384_micro/native384_summary.json` |

## Finding

The tutorial and cross-condition protocols differ in both trajectory roles and
spatial resolution. The cross-condition outcome therefore cannot identify wall
temperature, or any other individual physical quantity, as the cause of an
architecture-ranking change.

## Corrections made

The abstract/result numbers were not altered. The manuscript’s contribution,
central-finding statement, split-figure caption, and discussion now state that
the independent protocol also differed in spatial resolution. Causal language
about a temperature-driven mechanism is not used as a conclusion.

`RESOLUTION_CONFOUND_AUDIT = PASS` — the confound is explicit; no causal
temperature interpretation is retained.
