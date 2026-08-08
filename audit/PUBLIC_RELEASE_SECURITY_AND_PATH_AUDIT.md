# Public Release Security and Private-Path Audit

## Scope

The intended public artifact is the filtered `public_release/` staging tree,
created by `scripts/prepare_public_release.py`. The local source repository is
not itself the intended upload because it retains journal-facing/historical
materials and absolute local provenance paths.

## Checks

- High-confidence secret scan searched for private-key headers, assigned API-key,
  secret, password, token, and authorization-header patterns.
- Private-path scan searched text artifacts for `/Users/`, `/home/`,
  `/private/`, `/tmp/`, `/var/`, `C:\\`, `D:\\`, and the local username.
- Result: **PASS** for the filtered staging tree; neither scan returned a match.

## Controlled transform

Experiment/result records in the source tree retain incidental absolute local
checkpoint paths. The staging script replaces only those text paths with
`<local-path-redacted>` and documents the transform in
`PUBLIC_RELEASE_TRANSFORM.md`. Numerical fields, source hashes, and scientific
labels are unchanged.

No credential was found, exposed, or removed.
