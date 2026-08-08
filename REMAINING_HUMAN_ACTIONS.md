# Remaining Human Actions

Only actions requiring the author are listed here.

1. **Install the supplied MIT license.** Add the exact approved `LICENSE` file
   at the repository root. This is required because README/CFF/Zenodo metadata
   identify MIT but no license text is present. Verify with `test -f LICENSE`
   and by checking the public repository after release.
2. **Provide an elsarticle-capable TeX environment.** Install a TeX distribution
   containing `elsarticle.cls`, then compile `manuscript/manuscript_elsarticle.tex`
   from a clean directory. This is required for the manuscript-PDF gate. Success
   means no fatal/undefined citation/reference/missing-file errors and a visually
   inspected current PDF.
3. **Publish the intended GitHub release.** Authenticate as `RealmeBTI`, push
   branch `main` and annotated tag `v1.0.1` to `bubbleml-submission`, add the
   root `LICENSE`, and create a public release. Verify anonymously that the
   README, LICENSE, tag, release commit, and intended public files are visible.
4. **Archive the verified GitHub release in Zenodo.** In the author’s Zenodo
   account, enable the repository integration, archive the public `v1.0.1`
   release, and verify creator, ORCID, license, version, and repository metadata.
   Success is a publicly resolving DOI. Do not edit an archived version; add a
   new version if the DOI must be inserted into repository/manuscript metadata.
5. **Provide authorized data/checkpoint provenance if full retraining is claimed.**
   Supply official data URLs/licenses plus the complete checkpoint and
   cross-condition per-seed provenance. Verify with a fresh raw-data-to-checkpoint
   run. Without this, keep the release described as stored-result reproducible only.
6. **Decide on optional graphical abstract and portal declarations.** IJHMT
   encourages a graphical abstract; assess the final publisher AI/disclosure
   fields and upload requirements in the live portal. Verify against the current
   journal submission checklist before submission.
