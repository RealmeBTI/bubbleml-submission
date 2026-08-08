# Public-Release Staging Transform

`scripts/prepare_public_release.py` produces the `public_release/` staging tree
from a deliberate allowlist. It excludes journal-only submission attachments,
checked submission PDFs, local archive ZIPs, historical phase notes, build/cache
files, and source/checkpoint directories.

The source evidence files retain absolute local checkpoint references for audit
traceability. In the public staging tree only, the script replaces incidental
absolute local paths in text artifacts with `<local-path-redacted>`. This is a
privacy transformation only: it does not change numerical results, hashes,
experiment labels, model names, seeds, or scientific conclusions. The redacted
checkpoint paths refer to external/unavailable checkpoint binaries as declared in
`CHECKPOINT_MANIFEST.md` and `ARTIFACT_GAPS.md`.
