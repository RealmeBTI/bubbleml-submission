# Claim–Evidence Matrix

| Claim | Location | Evidence | Strength | Reviewer risk | Action |
|---|---|---|---|---|---|
| Tutorial T-FNO/U-Net trade-off exists | Abstract; 4.1 | Retained 11-seed paired metrics and self-test | SUPPORTED | Moderate | Retain, scoped to tutorial split |
| Tutorial ranking generalizes | Previously implicit in early framing | Cross-condition 5-seed summary does not replicate it | UNSUPPORTED | Critical | Removed; manuscript says no generalization is established |
| Cross-condition results favor U-Net descriptively | Abstract; 4.4 | `multitraj96/report_summary.json`, n=5, Holm=1.0 | SUPPORTED as descriptive only | Moderate | Retain with no superiority claim |
| Ranking change is caused by wall temperature | Potential causal interpretation | Designs differ in condition and 48×48/96×96 resolution | UNSUPPORTED | Critical | Explicitly disclaimed |
| Bounded alpha prevents out-of-range decoded alpha | 3.3; 4.2 | Bounded head construction and reported range | SUPPORTED | Low | Retain |
| Divergence penalty passes tutorial mass non-inferiority | 4.3 | 11-seed stored result, p=.00048828125 | SUPPORTED | Moderate | Retain, tutorial-scoped |
| Divergence benefit generalizes across conditions | 4.4; 5.2 | 5-seed compact summary, Holm=1.0 | PARTIALLY SUPPORTED | High | Say directionally/descriptively only |
| Dry-area proxy validates CHF detection | 4.5 | No verified CHF events/heat-flux labels | UNSUPPORTED | Critical | Explicitly rejected; proxy-only |
| Full retraining is reproducible | Section 7 | Raw data/checkpoints unavailable | UNSUPPORTED | Critical | State Level 1 supported, Level 3 unsupported |

`CLAIM_EVIDENCE_AUDIT = PASS` after the stated rewrites and evidence limits.
