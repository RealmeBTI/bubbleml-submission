# Recorded SHA-256 Checksums

These values come from the final manuscript, phase reports, and direct local
verification of four representative checkpoints. Files not present in this
repository are marked external and cannot be re-verified from this checkout.

## Tutorial 48 x 48 source files

| File | SHA-256 | Status |
|---|---|---|
| `Twall-103.hdf5` | `25b305661dee59cf5df49eb2563a4ed08f79664ba377e57877fcda5a948956dd` | external; manuscript train source |
| `Twall-106.hdf5` | `4308e5be884c3edcf301e9c12bff8d499d53729be3820aa18e255a5152fbd004` | external; manuscript validation source |
| `Twall-100.hdf5` | `5bf2539628c3595f39517c466f6971da76f137358771592c14ad1a5881e4d1bf` | external; manuscript test source |

## Legacy native-resolution archive and members

| File | SHA-256 |
|---|---|
| `pool-boiling-subcooled-fc72-2d.tar.gz` | `2eba140d74cbb7b01a55f0684227dea94306aea516a0f864831485d31d25f655` |
| `Twall-79.hdf5` | `c550dab2e2d5db4ecb7ccc159aefba2a43ab61c50d6d22a0a5322d2a45ad07df` |
| `Twall-81.hdf5` | `16b6cae48b50cb06a202e0f2c56585caf66eb6919e060b61dc7902026ab84452` |
| `Twall-85.hdf5` | `4f761caf8efcd66f93bcb55c36eea72876d83f85b8b30526a1b48dfeeb7e8dda` |
| `Twall-90.hdf5` | `35c859305795fda3a59ea16343d75a611ef4e89c7bacfa05c273b47bcc2d7240` |
| `Twall-95.hdf5` | `75809930d09d013024a76c0695f28f02c6785183e6d402285486fba334b65338` |
| `Twall-98.hdf5` | `1c3e4f23908ce6137d88abb8beb438ac08996ffbf191c6d91935d606bafdeb15` |
| `Twall-100.hdf5` | `8529a1b55613449dbbf99c936ce5f8308abfac92fe856891a9b337bd7f2e949e` |
| `Twall-103.hdf5` | `4ebc2f95c61fa64b4422f51603a35f19a55add15093fdee435db0558d4d458e1` |
| `Twall-106.hdf5` | `1b035a9cd8c9b765035bfe88ba2993aee96c52e5df6a8e2c4d32f51b8ca8db45` |
| `Twall-110.hdf5` | `874a07784d0120b402438d69bf66dd04191bd76ac1eb4b8151ad2ddec55134fd` |

The same Twall names have different hashes between tutorial and legacy releases
because they are different released files/resolutions. They are not interchangeable.

## Representative checkpoints

| Checkpoint | Bytes | SHA-256 | Verification |
|---|---:|---|---|
| `phase1_gpu_decisive/tfno_seed_9999.pt` | 4,185,773 | `f85e4b3811e721abed3ede47b3b9701b2525aad36c60ddb59d766c7fb0738bab` | direct local hash; also recorded in Phase 4 |
| `phase1_gpu_decisive/unet_seed_7.pt` | 31,106,427 | `58173aca6b36dbcb2b748a81549435b7288bbbd1cb91dacf97a25d9746feb3d8` | direct local hash; also recorded in Phase 4 |
| `lambda_sensitivity_030/hybrid_div_seed_42.pt` | 4,781,797 | `b80f5a23aaf13a88f536bee9e95ce85b8fcee1af62a6a4c6916c0ffcd06c7fb6` | direct local hash during submission assembly |
| `lambda_sensitivity_030/hybrid_div_seed_9999.pt` | 4,782,129 | `ed5048981a6ff6252cbdec265733de49b9abf019c9f1099bd0f9605851edfcf9` | direct local hash during submission assembly |

## Other recorded artifact hashes

| SHA-256 | Artifact | Provenance / verification |
|---|---|---|
| `7cfd11a642168b2c845addf79cdfba2191664b1a4f5096ea07149753b7e58b43` | `benchmark_results/multitraj96/report_summary.json` | Direct local SHA-256 recomputation; compact audited 96×96 cross-condition summary. |
| `492057863f155b49ab2d249dfdacbf6d855aa2fed8882185794cb5ce2cd8d2c6` | `benchmark_results/multitraj384_micro/native384_summary.json` | Direct local SHA-256 recomputation; native-384 one-epoch feasibility summary. |
| `7c4f8e743b89543c7e8a009f01a42f88b2ece7abd981623cbed02731dd100154` | Unassigned, provenance unrecoverable from this checkout | Phase history identifies it only as a temporary cloud upload bundle at `/private/tmp/ddpinns-future-work.tar.gz`; the bundle bytes are absent, so no local hash confirmation or archival role is claimed. |
