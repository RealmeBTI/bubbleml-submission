# BubbleML Comparison Verification

The source consulted is the verified BubbleML bibliographic record and the
existing comparison audit. “NOT REPORTED” means this audit did not locate a
description in the original neural-PDE benchmark; it does not assert absence.

| Feature | BubbleML original | This work |
|---|---|---|
| Multiple trajectories | YES (79 simulated conditions reported) | YES |
| Multi-objective interface/conservation metrics | NOT REPORTED | YES |
| Multi-seed paired testing | NOT REPORTED | YES |
| Cross-condition architecture replication | NOT REPORTED; heat-flux holdout CV reported | YES, protocol also differs in resolution |
| Output-validity constraints | NOT REPORTED | YES, bounded alpha head |
| Predeclared decision gates | NOT REPORTED | YES |
| Artifact release | YES, data/code/model-zoo reported | PARTIAL, retained results/code only |
| Reproducibility self-test | NOT REPORTED | YES, stored-result scope |

The manuscript table uses this wording and does not convert “NOT REPORTED” to
“NO.” `BUBBLEML_COMPARISON = PASS`.
