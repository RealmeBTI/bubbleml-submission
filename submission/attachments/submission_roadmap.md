# CMAME Submission Roadmap

## Journal-specific requirements verified on 2026-08-14

The live *Computer Methods in Applied Mechanics and Engineering* (CMAME) Guide
for Authors requires editable source files, a concise factual abstract of no
more than 250 words, a data-availability statement at submission, funding and
competing-interest declarations, and CRediT roles. CMAME uses
single-anonymized review, so the authored title page remains appropriate.

The current manuscript has a 229-word abstract, numbered `elsarticle-num`
references, a data-availability section, CRediT statement, funding statement,
and competing-interest declaration. Highlights and a graphical abstract are
encouraged by the guide; this package provides both. The graphical abstract is
a manually authored vector schematic because CMAME does not permit
generative-AI artwork in submitted figures.

## Submission files prepared

1. Main editable LaTeX manuscript and compiled review PDF.
2. CMAME-focused cover letter.
3. Five highlights, each below the stated 85-character limit.
4. Vector graphical abstract (`cmame_graphical_abstract.tex` and PDF).
5. CRediT, funding, competing-interest, and data-availability statements in
   the manuscript and in `author_statements_and_coi.md`.
6. Reproducibility manifest, audit reports, and source figure scripts.

## Author action required before upload

1. Supply a maximum-100-word biography and a passport-type photograph.
2. Confirm the exact generative-AI disclosure statement in
   `cmame_author_actions.md`; CMAME requires it if AI-assisted manuscript
   preparation was used.
3. Approve a new immutable public release that includes the checkpoint-retaining
   CUDA intervention artifact, then replace the temporary availability boundary
   with that release's verified DOI. Do not use the `v1.0.4` DOI as though it
   contained the new rerun.
4. Complete Elsevier's required declarations form in `.doc` or `.docx` during
   Editorial Manager submission.

## Final upload checks

1. Upload editable source, figures, and graphical abstract as separate files.
2. Verify every public repository/DOI link from a signed-out browser session.
3. Re-run the stored-result reproduction and full test suite from the release
   commit.
4. Ensure the author-supplied biography, photograph, and confirmed AI disclosure
   are included before selecting final submission.
