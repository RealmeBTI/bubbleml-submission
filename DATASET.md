# Dataset Manifest

## Committed evidence

The repository contains machine-readable benchmark summaries, per-seed result
artifacts where retained, experiment configurations, and derived figures under
`benchmark_results/`, `experiments/`, and `submission/figures/`.

## External source data

Raw BubbleML HDF5 sources are not committed. The exact tutorial-source hashes,
legacy archive hash, and the non-interchangeability of same-named files across
the two releases are recorded in `CHECKSUMS.md`. The complete cross-condition
raw archive is also external. No download URL is asserted because the local
materials do not establish the exact author-approved release location/version.

## Required boundaries

- Do not substitute synthetic data for the official source data.
- Verify a downloaded source against the applicable SHA-256 entry before use.
- The tutorial split is Twall-103 train, Twall-106 validation, Twall-100 test.
- The recorded cross-condition split is Twall 79/85/90/95 train, Twall 81
  validation, and Twall 98/110 independent test.

See `ARTIFACT_GAPS.md` for all unavailable data/export components.
