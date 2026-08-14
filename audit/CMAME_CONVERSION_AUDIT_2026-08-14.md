# CMAME conversion audit — 2026-08-14

## Scope and repository basis

This conversion was prepared on `codex/cmame-conversion`, a clean local branch
based on public GitHub `main` commit
`659065170d225a375b80e6a581283a3c644d32c5`. The reconciled canonical
manuscript and its verified CUDA artifacts were then transplanted from the
separate local audit checkout. No push, tag, GitHub release change, or Zenodo
action was performed.

## Live CMAME requirements checked

The current official CMAME Guide for Authors was checked on 2026-08-14:

- Guide: <https://www.sciencedirect.com/journal/computer-methods-in-applied-mechanics-and-engineering/publish/guide-for-authors>
- CMAME uses single-anonymized review; the author-identified title page remains appropriate.
- The abstract limit is 250 words; the converted abstract is 229 words.
- Highlights and graphical abstracts are encouraged. The supplied highlights meet the stated 3--5 bullet and 85-character-per-bullet guidance.
- The guide prohibits generative-AI or AI-assisted artwork in submitted figures, including graphical abstracts. The graphical abstract is a manually authored TikZ vector schematic.
- The guide requires editable source, a data statement, CRediT, funding and competing-interest declarations, and author biography/photo material.

## Changes

1. Changed the `elsarticle` journal metadata to *Computer Methods in Applied Mechanics and Engineering* while retaining the numbered `elsarticle-num` reference style.
2. Rewrote the cover letter for CMAME's computational-methods audience and inserted the confirmed checkpoint-retaining CUDA intervention result: mass MAE 0.09528 versus 0.16562, difference -0.07034, 95% CI [-0.07454, -0.06654], exact one-sided p=.000488281. It makes no cross-condition intervention claim.
3. Replaced the highlights with five CMAME-compliant bullets reflecting the confirmed conservation result and descriptive cross-condition scope.
4. Added manuscript Data availability, CRediT, Funding, and Declaration of competing interests sections.
5. Replaced the retired `fig1_pareto_front` / `fig:pareto-tradeoff` naming with `fig1_conservation_error_comparison` / `fig:conservation-error-comparison`.
6. Added `cmame_graphical_abstract.tex` and a compiled vector PDF. The 13.833 x 5.531 inch canvas corresponds to 1328 x 531 pixels at 96 dpi.
7. Extended the canonical checker to validate the CMAME cover letter, highlights, required manuscript sections, journal metadata, fresh CUDA result values, and conservation-error figure identity.

## Verification results

```text
CANONICAL MANUSCRIPT CONSISTENCY: PASS
tests/test_bubbleml_benchmark.py: 10 passed in 1.47s
tests/test_chf_rollout.py: 4 passed in 15.68s
tests/test_chf_rollout_stats.py: 1 passed in 0.80s
tests/test_paper_pipeline.py: 23 passed in 14.87s
Total: 38 passed, 0 failed
Stored-result reproduction: PASS
```

The main manuscript compiled to 27 pages. The title page, updated data-
availability/statement pages, and reference list were visually inspected. The
graphical abstract was rendered and visually inspected. No undefined references
or citations were reported by the build.

## Author-supplied items still required before submission

These cannot be fabricated and are recorded in
`submission/attachments/cmame_author_actions.md`:

1. A maximum-100-word author biography and passport-type photograph.
2. Author confirmation of the exact generative-AI disclosure statement.
3. Approval and completion of a new immutable public release containing the
   checkpoint-retaining CUDA intervention artifact, followed by a verified DOI
   update to the Data Availability Statement.
4. Completion of Elsevier's declarations form in editable Word format during
   Editorial Manager upload.
