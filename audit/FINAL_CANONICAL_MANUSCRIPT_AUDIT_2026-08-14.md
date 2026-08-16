# Final canonical manuscript audit — 2026-08-14

## Judgment

**The apparent manuscript regression was real as a workspace-selection error, not as a regression of the reconciled branch.** Work had been inspected in the separate stale checkout
`/Users/sbmahafujbondhon/antigravity_BUbbleML/bubbleml-submission` (branch
`manuscript/n11-resolution-audit`, commit `15ce5e8`) rather than the reconciled checkout
`/Users/sbmahafujbondhon/Documents/DD-PINNs/bubbleml-reconciliation` (branch
`codex/canonical-conservation`, current base commit `68582fa`). The stale checkout does not
contain commit `12e1876`; the active branch does, and `git merge-base --is-ancestor 12e1876
HEAD` returns success. No reconciled commit was reverted.

The reconciled manuscript is internally consistent after the corrections below. It is ready
for author review of this content checkpoint, but **no push, tag, GitHub release mutation,
Zenodo version, or CMAME conversion was performed**.

## Document identity

PASS:

- Exact title: *Phase-Resolved Neural Operator Learning for Boiling Flows: An Auditable Benchmark of Conservation Error*.
- Section 3.8 Nomenclature is present.
- `resolution_control_48x48` is identified as the canonical tutorial artifact.
- `phase1_gpu_decisive_tfno_unet_n11` is identified as retired MPS provenance.
- Section 3.2 identifies CUDA as the active tutorial campaign; MPS is not presented as active hardware.
- Markdown and generated LaTeX have the same Section 4 heading sequence (4.1–4.7).

The executable identity check reports:

```text
CANONICAL MANUSCRIPT CONSISTENCY: PASS
- Fresh 48x48 ledger matches manuscript/generated/canonical_fragments.json.
- Fresh checkpoint-retaining CUDA intervention matches the generated manuscript fragment.
- Exact title, Section 3.8, canonical artifact, and retired-artifact identity markers are present.
- Markdown contains the sole canonical-results marker in Section 4.1.
- Rendered LaTeX Section 4.1 contains all canonical statistics and no retired values.
- Rendered LaTeX Section 4 headings match the Markdown source.
```

## Definitive Holm result

`scripts/generate_canonical_statistics.py` implements standard monotonic step-down Holm
correction:

```python
adjusted = min(1.0, max(previous, (len(ordered) - rank) * row["exact_p"]))
```

The legitimate reason the mass-conservation result is not `.00390625` is that the frozen
comparison corrects the **complete 22-error-endpoint family**, including rollout counterparts,
after excluding compute-only descriptors. A post-hoc four-headline-metric family would be a
different analysis. Fresh executable output is:

```text
mass_conservation_mae: exact=0.0009765625 Holm=0.021484375
interface_temperature_jump_mae: exact=0.1962890625 Holm=1
interface_temperature_rmse: exact=0.234375 Holm=1
gwrmse: exact=0.890625 Holm=1
holm_family_size= 22
holm_step_down_monotonicity= True
```

Therefore Section 4.1 correctly renders unadjusted `p=.000976562` and Holm
`p=.0214844`. The manuscript now explains explicitly why `.00390625` is not the applicable
adjusted value. No `.0039` value is used as the Section 4.1 Holm result. The separate
`−0.00393` occurrence is a confidence-interval bound in the phase-bounding study, not a
p-value.

## Checkpoint-retaining CUDA intervention recovery

The new Kaggle run completed on two Tesla T4 GPUs with Python 3.12.13 and PyTorch
2.10.0+cu128. It used code commit
`71ccf511439d8837c177989a8d3afb0a82edbe8e`, the exact 11 frozen seeds, and the
byte-verified tutorial tensors and immutable T-FNO/U-Net baseline checkpoints.

Verified local bundle:

```text
path: audit/kaggle_hybrid_cuda_rerun_2026-08-14/hybrid_cuda_rerun_48x48_n11_reviewer_bundle.zip
size: 579,931,235 bytes
SHA-256: 1a73240957cc1a3375a1e146c76772b5551080e232926df9b4abefa33fa0a349
unzip -t: No errors detected
internal SHA256SUMS.txt: 621/621 files OK
prepared tensors: 498 .pt files
new intervention checkpoints: 22 .pt files
run-manifest seed records: 22 (11 hybrid_tfno + 11 hybrid_div)
```

The first resumable transfer appended a 467,733,603-byte duplicate suffix. It was not accepted
as evidence. The invalid concatenated transfer is preserved with suffix
`.transport_concatenated.invalid`; the canonical path above contains the clean first
579,931,235 bytes and independently matches the expected SHA-256. Scalar JSON files used by
the generator are byte-identical to their copies inside the verified ZIP.

## Intervention result now used in the manuscript

The canonical generator verifies that the rerun's T-FNO/U-Net baseline metrics exactly match
the canonical Section 4.1 artifact before accepting the intervention result.

Fresh CUDA results inserted into Section 4.2:

- Zero-penalty hybrid minus U-Net mass MAE: `+0.04152`, 95% CI
  `[+0.03611,+0.04632]`; it fails the frozen mass non-inferiority gate.
- Divergence hybrid (`lambda_div=.30`) mean mass MAE: `0.09528`; U-Net:
  `0.16562`; paired difference `−0.07034`, 95% CI
  `[−0.07454,−0.06654]`; exact one-sided gate `p=.000488281`; PASS.
- No interface regression relative to the zero-penalty hybrid was established.
- The fresh CUDA rerun covers the tutorial split only. No cross-condition divergence-hybrid
  numerical claim is made.

The generator marker `{{CANONICAL_HYBRID_RESULTS}}` replaces hand-entered Section 4.2 values.
`scripts/reproduce_reported_results.py` now reads the fresh CUDA artifact and reports PASS.

## Corrected stale content

Before:

> The divergence hybrid's conservation advantage transferred directionally: mass MAE 0.08669 versus U-Net's 0.11560 ...

After:

> An earlier divergence-hybrid cross-condition comparison came from the retired pipeline and is excluded from numerical claims. The checkpoint-retaining canonical CUDA rerun in Section 4.2 covers the tutorial split only; it therefore cannot establish intervention transfer to these independent conditions.

Repository-wide active-package searches found none of the retired intervention tokens
`0.09373`, `0.16586`, `−0.07212`, `0.08669`, `−0.02891`, `0.14499`, or `−0.02086` in the
Markdown manuscript, generated LaTeX, cover letter, highlights, or active submission
attachments. Historical audit/phase-history records retain those values and are not rewritten.
The canonical machine-readable ledger also filters the compact cross-condition summary to
T-FNO/U-Net only and records `hybrid_tfno` and `hybrid_div` under
`excluded_stored_models`; their historical source fields remain preserved but are not emitted
as current canonical results.

## Reviewer-critique fixes

1. **Methodological contribution foregrounded:** Section 3.5, contribution 5, and Section 5.2 now lead with decoded physical-coordinate FFT divergence and explain why finite differences in normalized space would compound discretization error. The text does not claim invention of spectral divergence regularization.
2. **Methodology-over-scale scope:** the Abstract and early Introduction explicitly present a representative five-trajectory case study and reject general architecture-selection claims.
3. **Results reordered:** generated Section 4.1 leads with the confirmed mass-conservation weakness before non-significant interface/global results; Sections 4.3 and 5.1 lead with the supported direction before power caveats.
4. **Computational-methods framing:** the Introduction connects the evidence question to neural PDE surrogate evaluation beyond boiling while retaining the thermal-fluid motivation.
5. **Contribution-5 status reconciled:** tutorial intervention is confirmatory on the checkpoint-retaining CUDA rerun; cross-condition intervention transfer is untested. Abstract, contribution list, Sections 4.2–4.3, Section 5.2, Future Work, cover letter, highlights, and reproducibility manifest now agree.

The unsupported retired-pipeline lambda-sensitivity figure was removed from the active
manuscript. The remaining dry-area trace was renumbered Figure 4, and all generated LaTeX
labels/references were rebuilt.

## Tests and reproducibility

Tests were run individually in the repository's working `.venv` (PyTorch 2.13.0). The parent
`../.venv` is cloud-placeholder/dataless and failed during `torch` import; that environment
failure is not counted as a test outcome.

```text
tests/test_bubbleml_benchmark.py: 10 passed in 1.37s
tests/test_chf_rollout.py: 4 passed in 15.72s
tests/test_chf_rollout_stats.py: 1 passed in 0.81s
tests/test_paper_pipeline.py: 23 passed in 14.77s
Total: 38 passed, 0 failed
```

Stored-result reproduction reports PASS for the canonical tutorial statistics and the fresh
CUDA intervention result. Logs are retained under `test_logs/` and reproduced outputs under
`reproduced_final_2026-08-14/`.

## PDF build and visual inspection

`latexmk -pdf -interaction=nonstopmode -halt-on-error` rebuilt
`manuscript/manuscript_elsarticle.pdf` (26 pages). There are no undefined citations,
undefined references, missing figures, or build-stopping errors. Minor TeX box warnings remain
for long monospaced artifact paths and do not clip visible content.

All 26 rendered pages were inspected as contact sheets; the title page, Sections 4.1–4.4,
limitations table, reproducibility statement, figures, and references were inspected at full
page resolution. The title/author block is correct, the floating metadata paragraph is absent,
the email is rendered by `\ead`, ORCID and DOI are hyperlinked, and the DOI is not malformed.

## Final checkpoint hashes

```text
e6187f5babd4bc2bd2734ed9793f6e86b2eb989f8954a4577ae8eb24beceada8  manuscript/full_manuscript.md
cd4d784d7daf3b05a7798841d986a4b7fb8641157abc758506174943aee0af2c  manuscript/manuscript_elsarticle.tex
22ba2707f419aa87308e2cf98f0b8d5e76e15110c374446ba7b1e565bf22f572  manuscript/manuscript_elsarticle.pdf
2160783c8792224c6b29341954cf4c3bcf4e08e47f8cf08715b1cb9c989549d0  manuscript/generated/canonical_statistics.json
1a73240957cc1a3375a1e146c76772b5551080e232926df9b4abefa33fa0a349  audit/kaggle_hybrid_cuda_rerun_2026-08-14/hybrid_cuda_rerun_48x48_n11_reviewer_bundle.zip
```

## Remaining evidence boundaries (not defects concealed as PASS)

- Cross-condition results remain a compact five-seed/two-trajectory summary; complete
  per-seed checkpoints and histories are not locally retained.
- The exploratory 96x96 paired confidence intervals remain unreconciled and are excluded from
  all numerical claims.
- The fresh intervention rerun does not test cross-condition transfer or lambda values beyond
  the frozen `.30` candidate.
- Native 384x384 training is feasibility-only, not a converged comparison.
- The CHF result is proxy-only; no verified sustained CHF transition is available.
- A tutorial field-snapshot figure is now technically possible from retained tensors and
  checkpoints but is not claimed or fabricated in this manuscript; cross-condition snapshot
  artifacts remain unavailable.
- The new CUDA intervention bundle is local and checksum-verified but is not yet in a new
  immutable public release. Publishing it requires separate explicit release approval.

These boundaries do not invalidate the scoped claims. They prevent a truthful audit from
declaring the broader scientific program limitation-free.
