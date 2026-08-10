# Change Log — n=11 Resolution-Control Integration

## Date: 2026-08-10
## Branch: manuscript/n11-resolution-audit
## Base: experiment/resolution-control-n11 (eb7884e)

---

## C01 — Add Section 3.8 (Methods)

**File:** manuscript/manuscript_elsarticle.tex
**Original:** Section 3.7 (CHF proxy) followed directly by section separator
**New:** New subsection 3.8 inserted after 3.7 before section separator
**Reason:** Document the exploratory same-trajectory 96x96 experimental setup,
  with explicit disclosure of all confounding factors
**Evidence:** experiments/resolution_control_96x96/ configs;
  audit_n11/control_matrix.md
**Affected section:** §3 Methods
**Scientific impact:** None to existing claims; adds confound disclosure

## C02 — Add Section 4.7 (Results)

**File:** manuscript/manuscript_elsarticle.tex
**Original:** Section 4.6 (computational cost) followed directly by Discussion
**New:** New subsection 4.7 inserted after 4.6, before section separator
**Reason:** Report n=11 paired differences and Holm-adjusted p-values for 96x96
  tutorial-split comparison; explicitly framed as exploratory
**Evidence:** benchmark_results/resolution_control_96x96/resolution_control_analysis.json;
  recomputed independently in audit (values match)
**Affected section:** §4 Results
**Numbers introduced:**
  - GWRMSE +0.10868 (Holm 0.00391) — n=11, 96x96
  - int-T RMSE +0.46219 (Holm 0.00977) — n=11, 96x96
  - jump MAE +0.21433 (Holm 0.00391) — n=11, 96x96
  - mass MAE +0.04906 (Holm 0.00391) — n=11, 96x96
**Forbidden language explicitly absent:** No causal claims; no "resolution causes"
**Scientific impact:** Adds exploratory observation; no existing claims changed

## C03 — Add paragraph to Section 5.1 (Discussion)

**File:** manuscript/manuscript_elsarticle.tex
**Original:** Section 5.1 ended after "which the current two-condition
  independent test cannot support"
**New:** Additional paragraph noting that the exploratory 96x96 result is
  directionally consistent with the cross-condition result, and treating
  this as hypothesis-generating rather than confirmatory
**Reason:** Connect the new exploratory observation to the existing discussion
  in a scientifically precise way
**Affected section:** §5.1 Discussion
**Scientific impact:** Strengthens motivation for future controlled study;
  no existing conclusions changed

## C04 — Add row to Section 5.5 Limitations table

**File:** manuscript/manuscript_elsarticle.tex
**Original:** Hardware and Reproducibility rows were the last rows
**New:** Additional row: "Exploratory resolution comparison" documenting
  confounds
**Reason:** Explicit limitation disclosure as required by publication standards
**Affected section:** §5.5 Limitations
**Scientific impact:** Adds limitation transparency; required per audit

## C05 — Add bullet to Section 6 (Future Work)

**File:** manuscript/manuscript_elsarticle.tex
**Original:** 7 future work bullets ending with CHF trajectory item
**New:** 8th bullet added: factorial resolution experiment
**Reason:** Document the specific experimental design that would be needed
  to attribute observed differences to resolution
**Affected section:** §6 Future Work
**Scientific impact:** None; documents a required future study

## C06 — Update Section 7 (Reproducibility)

**File:** manuscript/manuscript_elsarticle.tex
**Original:** Section 7 discussed tutorial artifacts and cross-condition
  summary, ending with Zenodo DOI sentence
**New:** Additional paragraph documenting the 96x96 exploratory artifacts:
  branch, commit, committed files, absent checkpoints, artifact boundary
**Reason:** Reproducibility transparency requirement
**Affected section:** §7 Reproducibility
**Scientific impact:** Adds artifact boundary documentation

## C07 — Create audit_n11/ directory and audit files

**Files created:**
- audit_n11/manuscript_audit.md
- audit_n11/claim_ledger.csv
- audit_n11/numerical_ledger.csv
- audit_n11/control_matrix.md
- audit_n11/reviewer_attack_report.md
- audit_n11/reproducibility_audit.md
- audit_n11/change_log.md (this file)
**Reason:** Required by publication engineering protocol

---

## Numerically Verified Values (No Change)

The following values from the existing manuscript were verified against artifacts
and are UNCHANGED:

| Value | Section | Artifact | Status |
|---|---|---|---|
| GWRMSE diff -0.05698 (Holm=1.0) | 4.1 | phase1_gpu_decisive_tfno_unet_n11 | VERIFIED |
| int-T RMSE diff -0.50190 (Holm=0.03516) | 4.1 | same | VERIFIED |
| jump MAE diff -0.43147 (Holm=0.02148) | 4.1 | same | VERIFIED |
| mass MAE diff +0.04494 (Holm=0.02148) | 4.1 | same | VERIFIED |
| hybrid mass MAE 0.09373 vs U-Net 0.16586 | 4.3 | lambda_sensitivity_030_n11 | VERIFIED |
| all cross-condition diffs (n=5, Holm=1.0) | 4.4 | multitraj96/report_summary.json | NOT RECOMPUTED from raw |
| T-FNO parameters 548,837 | 4.6 | phase1 JSON | VERIFIED |
| U-Net parameters 7,770,169 | 4.6 | phase1 JSON | VERIFIED |

## Values NOT Used (Superseded by n=11)

| Old value | New value | Location |
|---|---|---|
| GWRMSE 96x96 diff +0.12423 (n=7 preliminary) | +0.10868 (n=11 authoritative) | Used ONLY in audit records; NOT in manuscript |

STATUS: No superseded n=7 value appears in the revised manuscript.
