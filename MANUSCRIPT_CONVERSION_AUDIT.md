# Manuscript Conversion Audit

Audit date: 2026-08-08.

## Source identity

- The baseline supplied manuscript attachment has SHA-256
  `40c9d1ece71dae77b5251ca91f4525c7b8a4fa711717a2fff9ea19ca67b02f4d`.
- `manuscript/full_manuscript.md` was intentionally revised after that baseline
  to add verified citations, a protocol-comparison table, and two protocol
  diagrams. The baseline is retained in git history; the current source is the
  reproducible input for the assembled PDF.
- The five retained submission-attachment Markdown files are preserved except
  for the reproducibility manifest, which was corrected to remove an unsupported
  field-snapshot claim.

## Mechanical conversion

- Input: revised Markdown source with eight second-level sections, the supplied
  equations and tables, a protocol comparison table, and two vector diagrams.
- Output: `manuscript/manuscript_elsarticle.tex`, built with the `elsarticle`
  class and a numbered bibliography.
- Author, affiliation, corresponding-author, and journal fields remain bracketed.
- Existing numbered section titles are preserved and automatic duplicate section
  numbering is suppressed.
- The manuscript body is generated mechanically by
  `scripts/build_manuscript_tex.py`; its only post-conversion transforms are
  table widths, figure width, and formal citation commands for names already
  present in the Markdown source.

## Build and inspection

- The final PDF compiled with Tectonic without a LaTeX error or undefined citation.
- The resulting manuscript is 22 pages. Rendered inspection covered the protocol
  comparison table, checksum table, both new diagrams, and the citation-bearing
  related-work pages. A discovered checksum-table overlap was corrected and the
  PDF rebuilt before this audit was recorded.
- Minor nonfatal TeX box warnings remain for long hashes and technical tokens; no
  clipping or overlap was observed in the inspected output.

## Deliberately unresolved items

The manuscript has thirteen independently checked bibliography records. Generic
allusions not tied to a named record remain documented in
`BIBLIOGRAPHY_VERIFICATION.md`. The final journal and its live template
requirements still require author confirmation.
