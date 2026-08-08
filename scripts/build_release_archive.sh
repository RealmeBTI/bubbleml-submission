#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARCHIVE="output/bubbleml_submission_package.zip"
rm -f "$ARCHIVE"

/usr/bin/zip -q -r "$ARCHIVE" \
  README.md \
  LICENSE \
  CITATION.cff \
  ARTIFACT_GAPS.md \
  BIBLIOGRAPHY_VERIFICATION.md \
  CHECKSUMS.md \
  FIGURE_QA.md \
  MANUSCRIPT_CONVERSION_AUDIT.md \
  FINAL_IJHMT_PUBLICATION_STATUS.md \
  FINAL_IJHMT_PUBLICATION_SCORECARD.md \
  FINAL_PUBLICATION_REPORT.md \
  REMAINING_HUMAN_ACTIONS.md \
  REPRODUCIBILITY_SELFTEST.md \
  RELEASE_SHA256SUMS.txt \
  SUBMISSION_CHECKLIST.md \
  pyproject.toml \
  requirements.txt \
  requirements-submission.txt \
  environment.yml \
  bubbleml_benchmark \
  audit \
  scripts \
  tests \
  legacy \
  phase_history \
  experiments \
  benchmark_results \
  manuscript \
  submission \
  output/pdf \
  reproduced \
  -x '*/__pycache__/*' '*.pyc' 'tmp/*' 'manuscript/output/*' 'manuscript/*.pdf' 'manuscript/*.spl' '*.DS_Store'

echo "$ARCHIVE"
