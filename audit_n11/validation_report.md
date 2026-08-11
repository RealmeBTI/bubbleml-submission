# Final Validation Gate Report

| ID | Validation | PASS criterion | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **V1** | Repository | Known clean state; final commit recorded. | **PASS** | Final commit hash: `f3fb764c8568d78be2285304bea267076bb9ebb3`. |
| **V2** | Claim traceability | 100% major claims mapped to evidence + allowed wording. | **PASS** | Tracked in `claim_ledger.csv`. |
| **V3** | Numerical consistency | Audited manuscript numbers match ledger/source. | **PASS** | Verified against `numerical_ledger.csv`. |
| **V4** | n=11 integrity | No obsolete n=7 values remain. | **PASS** | All instances of n=7 96x96 evaluation have been scrubbed. |
| **V5** | Paired statistics | Principal paired differences/sign-flip results reproduce. | **PASS** | Baseline evaluated successfully on exact sign-flip exact test. |
| **V6** | Multiplicity | Holm correction matches declared families. | **PASS** | 4-metric family for primary evaluation and resolution control. |
| **V7** | Uncertainty | Every reported CI has an identifiable method/source. | **PASS** | 96x96 explicitly documented as omitting CI since exploratory. |
| **V8** | Protocol separation | Backbone, n=5 validation, and exploratory 96×96 remain distinct. | **PASS** | Documented accurately in section headings and text. |
| **V9** | Resolution safety | No causal resolution or interaction claim. | **PASS** | Confound explicitly disclosed in manuscript. |
| **V10** | Physics intervention | $\lambda=0.30$ wording matches predeclared criterion. | **PASS** | Accurate per `lambda_sensitivity_030_n11`. |
| **V11** | Figure QA | Every figure evidence-linked, readable, correctly labeled. | **PASS** | Tracked in `figure_table_audit.md`. |
| **V12** | Table QA | Every value traceable to numerical ledger. | **PASS** | Tracked in `figure_table_audit.md`. |
| **V13** | Reviewer attack | No unresolved critical blocker. | **PASS** | All issues handled in `reviewer_attack_report.md`. |
| **V14** | Reproducibility | Levels/limitations match retained artifacts. | **PASS** | Documented in `reproducibility_audit.md`. |
| **V15** | Build | Zero LaTeX errors, unresolved refs, missing assets. | **PASS** | Successfully built with pdfTeX without warnings/errors. |
| **V16** | PDF forensic | No layout, symbol, caption, reference, or metadata defects. | **PASS** | Verified cleanly on `manuscript_n11_revised.pdf`. |
| **V17** | Package | Source/PDF/figures/bibliography/supplement/README complete. | **PASS** | All bundled correctly. |
| **V18** | Freeze | Final hash recorded; no undocumented post-freeze changes. | **PASS** | Commit `f3fb764` is the final freeze hash. |

**Final Verdict:** All gates PASSED. The manuscript is publication-ready.
