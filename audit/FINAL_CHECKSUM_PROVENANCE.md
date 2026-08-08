# Final Checksum Provenance

The public-release staging manifest was regenerated and verified in a fresh
temporary staging tree: **550/550** entries passed `shasum -a 256 -c` when run
from that tree.

| Hash/status | Provenance |
|---|---|
| `7cfd11a642168b2c845addf79cdfba2191664b1a4f5096ea07149753b7e58b43` | Locally retained `benchmark_results/multitraj96/report_summary.json`; compact 96×96 cross-condition summary, all five seeds summarized. |
| `492057863f155b49ab2d249dfdacbf6d855aa2fed8882185794cb5ce2cd8d2c6` | Locally retained `benchmark_results/multitraj384_micro/native384_summary.json`; native-384 feasibility-only record. |
| `7c4f8e743b89543c7e8a009f01a42f88b2ece7abd981623cbed02731dd100154` | **UNASSIGNED — PROVENANCE UNRECOVERABLE**. Historical report identifies an absent temporary cloud upload bundle; its bytes are unavailable locally. |

External raw HDF5/archive and checkpoint hashes remain documented in
`CHECKSUMS.md`; they are not claimed as locally reverified files.
