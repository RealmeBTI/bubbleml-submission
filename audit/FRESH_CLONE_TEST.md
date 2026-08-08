# Fresh Local-Clone Test

## Target

The final annotated `v1.0.0` tag was cloned into a new directory under the
system temporary area. The clone was detached at `v1.0.0`; it was not run from
the working repository.

## Checks

1. Ran the dependency-free reviewer command:
   `python scripts/reproduce_reported_results.py --output-dir reproduced`.
   Result: **PASS**; stored tutorial paired statistics and lambda-0.30
   non-inferiority were recomputed.
2. Used the recorded project environment against the fresh clone:
   `python -m pytest -q`. Result: **38 passed**.
3. Generated the filtered public staging tree and verified its manifest:
   `shasum -a 256 -c RELEASE_SHA256SUMS.txt`. Result: **PASS** for every file.

The clean clone test validates committed stored-result analysis, code tests, and
release-staging integrity. It does not claim raw-data training reproducibility;
that remains limited by the external artifacts declared in `ARTIFACT_GAPS.md`.
