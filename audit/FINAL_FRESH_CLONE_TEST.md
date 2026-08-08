# Final Fresh-Clone Test

## Target

A new temporary clone was made from the local Git repository and checked out at
`ca0f645d242af0f209596ffc4b08850a5058acf7` (the audited source/package
commit). The test was not run from the original working directory.

## Executed checks

1. `python scripts/reproduce_reported_results.py --output-dir reproduced` —
   PASS; retained tutorial paired statistics and lambda=.30 non-inferiority
   were recomputed.
2. `python -m pytest -q` — **38 passed**; no skipped or expected-failure output
   was reported.
3. `python scripts/prepare_public_release.py --output-dir <fresh-temp-stage>`
   followed by `shasum -a 256 -c RELEASE_SHA256SUMS.txt` from that stage —
   **550/550** manifest entries verified.

## Boundary

The subsequent final documentation/tag commit changes audit/report metadata
only; it does not alter code, retained numerical result artifacts, PDFs, or the
release package tested above. This test does not claim raw-data training or
checkpoint reproduction.

`FRESH_CLONE = PASS`
