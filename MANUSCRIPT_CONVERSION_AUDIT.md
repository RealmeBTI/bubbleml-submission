# Manuscript Conversion Audit

Audit date: 2026-08-04.

## Source identity

- The retained source `manuscript/full_manuscript.md` has SHA-256
  `40c9d1ece71dae77b5251ca91f4525c7b8a4fa711717a2fff9ea19ca67b02f4d`.
- That hash is byte-identical to the manuscript attachment supplied for this task.
- All five retained attachment Markdown files are byte-identical to the supplied
  files; their hashes are recorded in `SUBMISSION_CHECKLIST.md`.

## Mechanical conversion

- Input: 234 lines, eight second-level sections, and the supplied equations and
  tables.
- Output: `manuscript/manuscript_elsarticle.tex`, built with the `elsarticle`
  class and a numbered bibliography.
- Author, affiliation, corresponding-author, and journal fields remain bracketed.
- Existing numbered section titles are preserved and automatic duplicate section
  numbering is suppressed.
- The manuscript body is generated mechanically by
  `scripts/build_manuscript_tex.py`; it does not rewrite claims.

## Build and inspection

- The final PDF compiled with Tectonic 0.16.9 without a LaTeX error or undefined
  citation.
- The resulting manuscript is 19 pages.
- Every page was rasterized and inspected in a contact sheet; detailed checks were
  also made on pages containing wide tables and the reference list.
- Minor nonfatal overfull-box warnings remain (maximum observed 9.29 pt), caused
  by unbreakable technical tokens. No clipping was observed in the rendered PDF.

## Deliberately unresolved items

The supplied manuscript does not provide enough information to construct a
complete bibliography. Identifiable works were checked and added; prose
allusions that cannot be safely mapped to a publication remain `[VERIFY]` as
listed in `BIBLIOGRAPHY_VERIFICATION.md`. The final journal and its live template
requirements also require author confirmation.
