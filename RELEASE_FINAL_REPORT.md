# Release Final Report

## Project identity

- Project: BubbleML Physics-Aware Benchmark.
- Phase 1 source handoff: `db21b9412364a6bfb7c9ccae2a50cf76dd3dff0c`.
- Final source identity: the `v1.0.0` Git tag created for this release. The
  canonical final commit is the commit resolved by that tag; it is intentionally
  not embedded as a self-referential hash in this committed document.

## Scientific verification

The citation, hash, split, comparison-table, numerical-consistency, and figure
audits are in `audit/`. The central result is conditional: T-FNO has tutorial
interface-fidelity advantages while U-Net has tutorial conservation advantage;
the five-seed cross-condition results descriptively favor U-Net on all primary
T-FNO comparison metrics but are not Holm-confirmatory. The lambda-0.30
divergence hybrid has the retained tutorial conservation non-inferiority result.

Two historical hashes are locally matched; one remains unassigned. Compatible
field-snapshot inputs are unavailable and no substitute was created.

## Reproducibility

Code, stored-result analysis, and retained statistical analyses are reproducible
within the declared artifact boundary. Figure reproducibility is partial because
field snapshots are unavailable. Training and end-to-end reproducibility are not
supported from this checkout because raw data, complete checkpoints, and complete
cross-condition exports are absent. See `REPRODUCIBILITY_STATUS.md`.

## Local Git

The project is a local Git repository with a Phase 2 baseline checkpoint. The
final commit/tag verification and fresh-clone report are completed as part of the
release finalization sequence.

## GitHub and Zenodo

- GitHub repository: NONE (no configured remote or verified authenticated account).
- GitHub release: NONE.
- Zenodo record: NONE.
- DOI: NONE.

No GitHub or Zenodo publication is claimed. `zenodo_metadata.json` is a local
blocking-metadata record, not a deposition payload.

## Release verification

The final scorecard, test report, figure audit, checksum verification, security
scan, private-path scan, and fresh-clone test are recorded in the root and
`audit/` directories. The filtered `public_release/` staging tree is generated
by `scripts/prepare_public_release.py`; it excludes journal-only files and
redacts incidental local absolute paths in public text copies.

## Human actions

1. Supply approved authors/creators and a code license.
2. Provide an `elsarticle`-capable TeX engine and rerun the manuscript build gate.
3. Make any intended external data/checkpoints available with authorized URLs.
4. Authenticate and authorize GitHub publication, then create/verify the public release.
5. Authenticate and authorize Zenodo deposition, then verify the resulting record and DOI.
