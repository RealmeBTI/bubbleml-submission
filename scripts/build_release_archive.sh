#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARCHIVE="output/bubbleml_submission_package.zip"
rm -f "$ARCHIVE"

/usr/bin/zip -q -r "$ARCHIVE" \
  README.md \
  ARTIFACT_GAPS.md \
  BIBLIOGRAPHY_VERIFICATION.md \
  CHECKSUMS.md \
  FIGURE_QA.md \
  MANUSCRIPT_CONVERSION_AUDIT.md \
  REMAINING_HUMAN_ACTIONS.md \
  REPRODUCIBILITY_SELFTEST.md \
  SUBMISSION_CHECKLIST.md \
  pyproject.toml \
  requirements.txt \
  requirements-submission.txt \
  environment.yml \
  bubbleml_benchmark \
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
  -x '*/__pycache__/*' '*.pyc' 'tmp/*'

echo "$ARCHIVE"
