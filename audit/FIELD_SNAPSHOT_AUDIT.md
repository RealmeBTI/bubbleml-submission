# Field-Snapshot Audit

## Search result

The repository-wide checkpoint/data search found no committed `.pt`, `.pth`,
`.ckpt`, raw HDF5, or compatible field-array binary. `CHECKPOINT_MANIFEST.md`
and `ARTIFACT_GAPS.md` independently state that the complete checkpoint set and
cross-condition checkpoint provenance are unavailable. No compatible
tutorial-split T-FNO/U-Net checkpoint pair was found either.

## Decision

No `fig5_field_snapshots.pdf` or `.png` was created. The existing workflow
diagram remains `fig5_benchmark_workflow.*`; it is not a field comparison and
is not relabeled. Creating a prediction/ground-truth panel would require all of
the following, none of which is locally verified: checkpoint identity,
architecture, split, preprocessing, normalization, test frames, and output
channels.

`FIELD_SNAPSHOT = NOT GENERATED; PROVENANCE UNAVAILABLE`
