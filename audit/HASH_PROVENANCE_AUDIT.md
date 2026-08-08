# Hash Provenance Audit

| SHA-256 | Artifact/status | Verification |
|---|---|---|
| `7cfd11a642168b2c845addf79cdfba2191664b1a4f5096ea07149753b7e58b43` | `benchmark_results/multitraj96/report_summary.json`; compact 96×96 cross-condition summary | Recorded in `CHECKSUMS.md`, phase history, and `RELEASE_SHA256SUMS.txt`; retained local artifact identified |
| `492057863f155b49ab2d249dfdacbf6d855aa2fed8882185794cb5ce2cd8d2c6` | `benchmark_results/multitraj384_micro/native384_summary.json`; native-384 one-epoch feasibility summary | Recorded in `CHECKSUMS.md`, phase history, and `RELEASE_SHA256SUMS.txt`; retained local artifact identified |
| `7c4f8e743b89543c7e8a009f01a42f88b2ece7abd981623cbed02731dd100154` | Unassigned, provenance unrecoverable | Phase history identifies an absent temporary upload bundle at `/private/tmp/ddpinns-future-work.tar.gz`; bytes are not in the checkout, so no local recomputation is possible |

The third hash is retained rather than deleted. It is not claimed as a released
artifact, checkpoint, or result file.

`HASH_PROVENANCE = PASS` for documentation; the absent bundle remains
`PROVENANCE UNRECOVERABLE`.
