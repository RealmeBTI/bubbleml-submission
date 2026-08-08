# Reproducibility Self-Test

Initial test date: 2026-08-04. Result: **PASS**.

## Final-audit rerun (2026-08-08)

From the current repository source, the documented command
`python scripts/reproduce_reported_results.py --output-dir reproduced` completed
with `PASS`. It recomputed the retained tutorial paired statistics and the
lambda=.30 non-inferiority check. The full test command `python -m pytest -q`
executed 38 tests with **38 passed** and no skips or expected failures reported.

This rerun remains a stored-result test, not an assertion of raw-data training
reproducibility.

## Reviewer simulation

A local commit was cloned into a newly created directory and executed with a new
Python 3.12.7 virtual environment. The test used only the public command in the
README and no installed third-party packages.

```bash
git clone /Users/sbmahafujbondhon/Documents/DD-PINNs/bubbleml-submission \
  /private/tmp/bubbleml-reviewer.ssGUhj/repo
/Users/sbmahafujbondhon/Documents/DD-PINNs/.venv/bin/python -m venv \
  /private/tmp/bubbleml-reviewer.ssGUhj/venv
cd /private/tmp/bubbleml-reviewer.ssGUhj/repo
/usr/bin/time -p /private/tmp/bubbleml-reviewer.ssGUhj/venv/bin/python \
  scripts/reproduce_reported_results.py --output-dir reproduced
```

Wall time for the reviewer-facing reproduction command was 0.06 seconds
(`user 0.04`, `sys 0.00`) on the assembly machine. This time excludes cloning and
virtual-environment creation.

## Reproduced results

The clean clone independently recomputed from stored per-seed JSON:

- Tutorial T-FNO minus U-Net interface-temperature RMSE difference:
  `-0.50189749`, 95% archived bootstrap interval
  `[-0.74065434, -0.28300856]`, exact two-sided sign-flip
  `p=0.001953125`, Holm-adjusted `p=0.03515625`.
- Tutorial T-FNO minus U-Net mass-conservation MAE difference:
  `+0.04493574`, interval `[+0.03852948, +0.05122263]`, exact
  `p=0.0009765625`, Holm-adjusted `p=0.02148438`.
- Divergence hybrid (`lambda_div=0.30`) mass-conservation mean `0.09373474`
  versus U-Net `0.16585691`; difference `-0.07212217`, archived interval
  `[-0.07939724, -0.06534623]`, exact one-sided `p=0.000488281`, and the
  archived non-inferiority decision `True`.
- `reproduced/fig2_dry_area_trace.svg`, SHA-256
  `f75383f1e62b288be6561220fd434b45f41d3506b44eadf161b8bab3a5200e10`.

## Discrepancies

None. The generated SVG and text report were byte-identical to the committed
reference outputs (`git status --short` returned no changes).

## Scope

This is a stored-evidence reproducibility test, not a raw-data retraining test.
The full ML test suite was separately run in the recorded pinned environment and
passed 38/38 tests. A full raw-data-to-checkpoint reviewer test remains blocked by
the external data/checkpoint and cross-condition export gaps declared in
`ARTIFACT_GAPS.md`; this limitation is not concealed by the PASS above.
