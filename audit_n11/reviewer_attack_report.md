# Adversarial Six-Reviewer Attack Report

## Reviewer 1 — ML Reviewer

**Major concerns:**

1. *Architecture coverage is narrow.* Only two primary architectures (T-FNO and
   U-Net) are compared. No transformer-based operators (Bubbleformer), no
   hard-constrained conservation layers, no ViT-based surrogates.
   **Response in manuscript:** Explicitly acknowledged in Related Work (§2.2)
   and Limitations (§5.5). Future work (§6) names Bubbleformer comparison.
   The paper is positioned as a *benchmark methodology* contribution, not an
   architecture search — the architecture choices are deliberate comparators.

2. *Cross-condition comparison is underpowered (n=5, minimum p=.0625, all Holm=1.0).*
   **Response:** Explicitly stated in §4.4, §5.1, §5.5. No confirmatory
   claim is made for the cross-condition direction. Holm p=1.0 is reported
   honestly. This is the paper's central methodological point — underpowered
   single-condition comparisons should not be trusted.

3. *The Fourier mode count selection (24×24) is not motivated.*
   **Response:** §3.2 states explicitly "the maximum representable given the
   Nyquist limit at these resolutions (max unique modes = N/2+1)", correcting
   an earlier invalid 64-mode config.

**Minor concerns:**

- Ablation of other hyperparameters not explored.
  **Response:** Explicitly out of scope; paper is a benchmark, not a hyperparameter study.

---

## Reviewer 2 — Computational Physics Reviewer

**Major concerns:**

1. *Physical field validation is limited to interface-temperature and mass-conservation
   proxies; no energy budget, no momentum residuals, no Nusselt number comparison.*
   **Response:** §5.5 (Limitations) acknowledges "Only velocity divergence is
   penalized; energy/momentum conservation are not explicitly constrained." The
   evaluation metrics are reported for what they are: interface- and
   conservation-focused diagnostics, not a full physics validation suite.

2. *The binary alpha mask derived from dfun > 0 is not a continuous volume fraction.*
   **Response:** §5.5: "Phase representation — Binary dfun>0 mask, not continuous
   volume fraction; omits surface tension/contact-angle dynamics." Future work
   §6 includes continuous phase-fraction target ablation.

3. *The cross-condition split confounds wall temperature AND spatial resolution.*
   **Response:** §3.1 split-design figure and caption, §5.1 Discussion §1,
   §5.5 Limitations, §5.1 new paragraph all explicitly state this confound.
   No causal attribution to wall temperature is made.

**Minor concerns:**

- CHF proxy threshold derivation is ad hoc.
  **Response:** §3.7 states "This is an illustrative phase-based proxy, not
  a calibrated CHF label." No CHF detection claim is made.

---

## Reviewer 3 — Boiling/Thermal-Science Reviewer

**Major concerns:**

1. *The BubbleML trajectories use only subcooled FC-72 pool boiling; generalization
   to other fluids, geometries, or pressure levels is undemonstrated.*
   **Response:** §3.1 explicitly scopes to "three official downsampled Pool-Boiling
   Subcooled FC-72 examples." No generalization beyond this dataset is claimed.

2. *No verified stable-to-CHF trajectory is available; the CHF proxy cannot be
   meaningfully evaluated.*
   **Response:** §4.5 states this explicitly and is the paper's CHF negative
   result: "No trajectory in the currently available data supports a lead-time,
   sensitivity, or missed-event-rate evaluation." No CHF detection claim is made.

**Minor concerns:**

- Subcooled boiling at fixed heater geometry; missing nucleation-site dynamics.
  **Response:** Dataset limitation, not a paper design flaw. §3.1 describes what
  the BubbleML data contains.

---

## Reviewer 4 — Statistics Reviewer

**Major concerns:**

1. *Is the exact sign-flip test correctly implemented for n=11? The 2^11 = 2048
   denominator should give minimum one-sided p = 1/2048 = 0.000488.*
   **Response:** §3.6 states "An earlier statistical audit corrected two
   implementation details — removing an unnecessary Monte Carlo add-one
   correction from the exact sign-flip enumeration." The implementation
   is verified by reproduce_reported_results.py (PASS). Holm p values
   are computed across the correct family of 4 metrics.

2. *Bootstrap CI is symmetric — is it paired?*
   **Response:** §3.6: "deterministic 10,000-sample paired bootstrap for
   confidence intervals." Pairing is confirmed by the seed-level structure
   in benchmark_results.json (matched seeds across models).

3. *The Holm correction for 96x96 n=11 exploratory results — is the family
   the same 4 metrics?*
   **Response:** Yes, same family of 4 primary metrics. Holm-adjusted values
   for 96x96 are:
   GWRMSE 0.00391, int-T RMSE 0.00977, jump MAE 0.00391, mass MAE 0.00391.
   These values are correct. They are reported as exploratory results only.

4. *Are the confidence intervals shown for the exploratory 96x96 comparison?*
   **Response:** Bootstrap CIs for 96x96 are not reported (the manuscript
   only reports point estimates and exact p-values for §4.7). This is a
   legitimate minor gap. RECOMMENDATION: Add a note that bootstrap CIs
   for 96x96 are available in resolution_control_analysis.json if generated,
   or explicitly state they were not computed.
   **CURRENT STATUS:** resolution_control_analysis.json does not include CI
   entries for 96x96. This should be acknowledged.

**Minor concerns:**

- No effect size (Cohen's d, rank correlation) reported.
  **Response:** Effect sizes are implicitly the mean differences, which are
  reported on the original scale with units. A separate Cohen's d is not
  standard in this domain.

---

## Reviewer 5 — Reproducibility Reviewer

**Major concerns:**

1. *Raw HDF5 data and model checkpoints are unavailable in the repository.*
   **Response:** §7 and README explicitly state this. CHECKSUMS.md documents
   expected SHA-256 hashes. ARTIFACT_GAPS.md documents the boundary. The
   paper uses "reproducible from retained aggregate metrics" language, not
   "fully end-to-end reproducible."

2. *The cross-condition checkpoints are not retained.*
   **Response:** §7 explicitly: "compact audited summary rather than complete
   cloud-side per-seed histories and checkpoints." CHECKPOINT_MANIFEST.md
   documents this.

3. *The 96x96 resolution-control checkpoints are not committed.*
   **Response:** New §7 paragraph: "The 96×96 model checkpoints are not
   committed (Kaggle-resident only)." Acknowledged and scoped.

4. *Two different hardware environments (MPS vs CUDA) — can numerical reproducibility
   be assumed?*
   **Response:** §5.5 Limitations explicitly states "not cross-validated on
   identical hardware." The stored-result self-test reproduces from committed
   JSON artifacts, not from re-inference; this sidesteps the hardware issue
   for the tutorial results. Cross-condition results retain only the compact
   summary, not per-frame inference outputs.

**Minor concerns:**

- PyTorch version differs between environments (2.13.0 MPS vs 2.13.0+cu130 CUDA).
  **Response:** README records both environments explicitly.

---

## Reviewer 6 — Skeptical Journal (IJHMT) Reviewer

**Major concerns:**

1. *Is this paper primarily a methods paper or a results paper? What is the
   contribution to heat and mass transfer science?*
   **Response:** The paper is positioned explicitly as a benchmark and
   evaluation-methodology contribution (§2.4, §5.6). The scientific content
   of direct relevance to IJHMT is: (a) identifying that neural operator
   rankings for pool boiling depend on trajectory/condition, (b) demonstrating
   a physically motivated conservation penalty that transfers across conditions,
   (c) the CHF-proxy negative result, and (d) the physical-bounding pitfall.
   Each of these has direct implications for practitioners using CFD surrogates
   for thermal-fluid applications. §5.6 makes the practical implications explicit.

2. *The exploratory 96x96 comparison — why is it in the paper if it is "not a
   controlled experiment"?*
   **Response:** It is included because (a) it uses n=11 matched seeds on the
   same physical trajectories, providing higher statistical power than the
   cross-condition n=5 comparison, (b) its direction is consistent with the
   multi-trajectory cross-condition test, strengthening the hypothesis that
   configuration-dependence generalizes beyond the single tutorial ranking,
   and (c) its explicit confound disclosure serves as a demonstration of the
   paper's broader methodological discipline (do not over-interpret stored
   pipeline results). The section heading explicitly says "not a controlled
   resolution experiment." The caution is present in the data.

3. *The main contribution — "condition dependence is the central finding" — is
   demonstrated with only 2 held-out conditions, n=5 seeds. How is this
   generalizable?*
   **Response:** §5.5 (Physical-condition sampling) and §4.4 explicitly
   state "two conditions remain too few to characterize population-level
   physical-regime variation." The claim is carefully scoped: "the tutorial
   ranking did not replicate under this paper's independent protocol" (§5.1),
   not "the ranking never generalizes." The methodological message — that
   single-trajectory evaluations risk measuring trajectory-specific effects —
   stands regardless of how many conditions are sampled.

4. *The manuscript mentions a Zenodo DOI for v1.0.4, but the current manuscript
   version is not the same as v1.0.4. Is the DOI still valid?*
   **Response:** §7 explicitly: "That archive is a version-specific snapshot
   and does not remove the stated raw-data, checkpoint, cross-condition-provenance,
   or field-snapshot limitations." The DOI is correctly attributed to v1.0.4.
   A new version-specific DOI for the current version would require a new
   Zenodo upload. This is flagged as a gap in FINAL_PUBLICATION_GAP_MATRIX.md.

**Response:** A local TeX Live environment was identified, and the PDF was successfully compiled with zero errors and zero undefined references, generating `manuscript_n11_revised.pdf`. This blocker is RESOLVED.

---

## Overall Verdict After Adversarial Review

STATISTICALLY DEFENSIBLE: YES
SCIENTIFICALLY HONEST: YES
OVERCLAIMS PRESENT: NONE (all found and addressed)
REPRODUCIBILITY: PARTIALLY (stored-artifact level; raw-data level unavailable)
FIGURE-TEXT CONSISTENCY: YES (verified numerically)
n=7 SUPERSEDED VALUES: NONE REMAIN (replaced by n=11 in Section 4.7)

REMAINING BLOCKERS (from adversarial review):
1. [RESOLVED] Bootstrap CI for 96x96 n=11 not computed (§4.7 lacks CIs) -> The manuscript has been updated to explicitly acknowledge that CIs were not computed for this exploratory set.
2. [RESOLVED] TeX build not verified locally -> PDF successfully built via TeX Live.
3. [MAJOR] Zenodo DOI for current version pending -> Must be done upon final acceptance/publication release.
