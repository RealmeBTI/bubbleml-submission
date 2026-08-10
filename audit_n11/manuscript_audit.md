# Manuscript Audit: BubbleML IJHMT Submission
# Scope: Integration of n=11 96x96 Resolution-Control Results

**Date:** 2026-08-10
**Branch:** manuscript/n11-resolution-audit
**Base commit:** experiment/resolution-control-n11 (eb7884e)

---

## 1. Repository Discovery Summary

### Files Inspected

| File | Purpose | Status |
|---|---|---|
| manuscript/manuscript_elsarticle.tex | Main LaTeX manuscript (982 lines) | PRIMARY |
| manuscript/full_manuscript.md | Markdown source | PRIMARY |
| manuscript/references.bib | Bibliography | PRESENT |
| manuscript/manuscript_elsarticle.pdf | Pre-compiled PDF | PRESENT |
| benchmark_results/phase1_gpu_decisive_tfno_unet_n11/benchmark_results.json | 48x48 n=11 primary results | AUTHORITATIVE |
| benchmark_results/resolution_control_96x96/benchmark_results.json | 96x96 n=11 merged results | AUTHORITATIVE (new) |
| benchmark_results/resolution_control_96x96/resolution_control_analysis.json | Resolution comparison analysis | AUTHORITATIVE (new) |
| benchmark_results/multitraj96/report_summary.json | Cross-condition (multi-traj) results | AUTHORITATIVE |
| benchmark_results/lambda_sensitivity_030_n11/ | Divergence penalty n=11 | AUTHORITATIVE |
| scripts/reproduce_reported_results.py | Numerical self-test script | PASSES (verified) |
| audit/CLAIM_EVIDENCE_MATRIX.md | Prior claim audit | REVIEWED |
| audit/RESOLUTION_CONFOUND_AUDIT.md | Resolution confound prior audit | REVIEWED |
| audit/IJHMT_RED_TEAM_REVIEW.md | Red-team review | REVIEWED |
| audit/FINAL_PUBLICATION_GAP_MATRIX.md | Gap matrix | REVIEWED |

### Key Missing Artifacts (MISSING_ARTIFACT)

- Raw HDF5 data checkpoints for 96x96 training (not committed, by design)
- Complete per-seed cross-condition training histories
- 96x96 model checkpoints
- Native-resolution (384x384) convergence results

---

## 2. Current Paper Map

### Section 1 — Introduction
- Purpose: Problem motivation (pool boiling, CHF, operator learning)
- Key claim: FNO variants may close BubbleML U-Net gap; ranking may be condition-dependent
- Evidence: BubbleML paper prior results as motivating context
- Weakness: None major; motivation is well-grounded
- Required changes: None to Introduction

### Section 2 — Related Work
- Purpose: Context for neural operators, boiling simulation, CHF
- Required changes: None

### Section 3 — Methods
- Purpose: Data, models, training, statistics
- Current 96x96 mention: Section 3.1 (cross-condition uses 96x96)
- New resolution-control experiment: NOT YET IN MANUSCRIPT
- Required changes: Add subsection 3.8 describing the resolution-control
  experimental design (same 3 trajectories, same seeds, 96x96 vs 48x48),
  with explicit confound disclosure

### Section 4 — Results
- Section 4.1: Tutorial-split T-FNO/U-Net Pareto (n=11, 48x48) — VERIFIED
- Section 4.4: Cross-condition non-replication (n=5, multi-traj 96x96) — VERIFIED
- New Section 4.7 needed: Exploratory resolution comparison (same trajectories,
  48x48 vs 96x96, n=11)
- Superseded n=7 values: GWRMSE +0.12423 must NOT appear; use n=11 +0.10868

### Section 5 — Discussion
- 5.1: Condition dependence — CORRECT; needs one paragraph on resolution observation
- 5.5: Limitations table — needs row for resolution-control confounds
- Required changes: Targeted additions to 5.1 and 5.5

### Section 6 — Future Work
- Already mentions resolution and expanded cross-condition testing
- Add: controlled factorial resolution experiment with matched preprocessing

### Section 7 — Reproducibility
- Add: n=11 resolution-control artifact and its provenance boundary

---

## 3. Scientific State Assessment

### Verified Core Results (UNCHANGED)
1. Tutorial 48x48 T-FNO/U-Net Pareto trade-off (n=11) — VERIFIED
2. Cross-condition non-replication (n=5, multi-trajectory 96x96) — VERIFIED
3. Divergence penalty mass-conservation non-inferiority (n=11) — VERIFIED
4. Physical bounding finding — VERIFIED
5. Decision-gate demonstration — VERIFIED
6. CHF proxy negative result — VERIFIED

### New Experimental Observation
- Resolution comparison (same tutorial trajectories, 48x48 vs 96x96, n=11) — EXPLORATORY ONLY
- HARD CONTROL GATE status: NOT_CONTROLLED
  (preprocessing horizon differs, hardware differs, checkpoints not cross-auditable)
- Scientific value: Documents ranking differences at matched trajectory conditions
  with n=11 statistical power; stronger than the n=7 preliminary analysis
- Correct framing: Exploratory observation, not causal resolution effect

---

## 4. Audit Conclusion

The existing manuscript is scientifically sound for its core claims.
The new n=11 96x96 resolution-control data should be integrated as
a clearly scoped supplementary exploratory observation.

No existing claims need to be removed or weakened.

The manuscript needs:
1. A new Methods subsection (3.8) describing the resolution-control protocol
2. A new Results subsection (4.7) reporting n=11 results with exploratory framing
3. Additions to Discussion 5.1 and 5.5 (limitations)
4. One new Future Work bullet
5. Updated Reproducibility section 7
6. A new audit file documenting the control matrix

STATUS: MANUSCRIPT IS SOUND — TARGETED INTEGRATION ONLY
