# BubbleML Comparison-Table Audit

Source consulted: the verified BubbleML bibliographic record and the manuscript
table in Section 2.4. “Not reported” means the original BubbleML publication did
not document the feature for its neural-PDE benchmark; it is not converted into
an assertion that the feature was absent.

| Feature | What BubbleML explicitly reports | Manuscript claim | Supported? | Correct wording |
|---|---|---|---|---|
| Multiple trajectories | 79 simulated conditions | Yes | Yes | Yes |
| Joint interface and conservation metrics | No documentation located for the neural-PDE benchmark | Not reported | Yes | Not reported |
| Multi-seed paired statistics | No documentation located | Not reported | Yes | Not reported |
| Cross-condition architecture replication | Heat-flux holdout cross-validation is reported; no matched architecture replication is documented | Not reported; heat-flux holdout cross-validation reported | Yes | Not reported |
| Physical output-validity enforcement | No documentation located | Not reported | Yes | Not reported |
| Predeclared decision gates | No documentation located | Not reported | Yes | Not reported |
| Artifact release | Data, code, and model zoo are reported | Partial | Yes | Partial |

No row is rendered as “No” where the available evidence only supports “Not
reported.”
