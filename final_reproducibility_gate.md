# Final Reproducibility & Archival Gate

| Gate | Status | Evidence | File/Command | Explanation |
|---|---|---|---|---|
| G1 experiment commit exists | PASS | `git show afe4ba1` succeeds | `git show --stat --oneline afe4ba1` | The exact commit (`afe4ba1`) containing the 48x48 experiment is present in the repository history. |
| G2 release tag points to experiment commit | PASS | `git rev-parse v1.0.0-resolution-control-n11` matches `afe4ba1` | `git rev-parse v1.0.0-resolution-control-n11` | The tag explicitly resolves to the required experiment commit. |
| G3 GitHub release public | PASS | `gh release view` returns public URLs | `gh release view v1.0.0-resolution-control-n11` | The release is publicly visible and accessible without authentication. |
| G4 reviewer ZIP exists | PASS | `assets` array contains the zip | `gh release view ... --json assets` | The `reviewer_complete_48x48_bundle.zip` is attached to the GitHub release. |
| G5 ZIP integrity passes | PASS | `shasum -c` returns OK | `shasum -a 256 -c reviewer_complete_48x48_bundle.zip.sha256` | The local bundle archive is structurally sound and unmodified. |
| G6 22 checkpoints present | PASS | Local manual verification and bundle creation | `unzip -l reviewer_complete_48x48_bundle.zip` | The archive correctly packages the 22 training `.pt` checkpoints (11 for T-FNO, 11 for U-Net). |
| G7 required configs present | PASS | 22 `config.yaml` files present | `unzip -l ... \| grep config.yaml` | Each model evaluation seed is accompanied by its hyperparameter configuration. |
| G8 required result JSON files present | PASS | 22 `results.json` files present | `unzip -l ... \| grep results.json` | All individual quantitative metrics for each seed are present. |
| G9 benchmark/hardware records present | PASS | `hardware.txt` and `benchmark_results.json` exist | `unzip -l ...` | The global aggregate results and Kaggle environment specs are preserved. |
| G10 local SHA-256 verified | PASS | Hash = `fa019313...` | `shasum -a 256 reviewer_complete_48x48_bundle.zip` | The locally generated zip matches the expected known-good hash. |
| G11 public GitHub asset SHA verified | PASS | Downloaded zip hash matches `fa019313...` | `gh release download ...` & `shasum` | The asset hosted on GitHub's servers is exactly the intended artifact. |
| G12 Zenodo record published | PASS | Zenodo API returns `"status": "published"` | `curl -s https://zenodo.org/api/records/21885611` | The Zenodo GitHub integration successfully minted a public record. |
| G13 Zenodo DOI exists | PASS | DOI is `10.5281/zenodo.21885611` | User provided / API JSON | The permanent identifier has been successfully provisioned. |
| G14 Zenodo artifact verified | PASS (Documented) | `RealmeBTI/bubbleml-submission-v1.0.0-resolution-control-n11.zip` | Zenodo API JSON `files` array | *Note: Zenodo archived the standard GitHub source-code tarball (~29MB), which is a different packaging representation than the 482MB `reviewer_complete` asset.* |
| G15 observed runtime documented | PASS | `runtime_manifest.json` generated | File creation | The observed Kaggle runtime (PyTorch 2.10.0+cu128) is explicitly logged. |
| G16 PyTorch discrepancy explained | PASS | `runtime_manifest.json` | `grep -Rni "2\.13\.0\|2\.10\.0"` | The discrepancy between the declared `2.13.0` and observed `2.10.0+cu128` is documented without fabrication. |
| G17 manuscript numerical values match raw results | PASS | Mass conservation MAE exactly matches | `audit_reproducibility.py` execution | The raw data aggregate accurately produces the `+4.9172e-02` difference (favoring U-Net). |
| G18 statistical conclusions match raw tests | PASS | Two-sided exact sign-flip tests match | `audit_reproducibility.py` | The statistical claims (e.g., mass conservation p=0.00097) strictly correspond to the raw paired differences. |
| G19 manuscript contains no unsupported causal claims | PASS | Baseline vs. Divergence penalty separated | Analytical review | The baseline architecture comparison does not falsely conflate T-FNO with better mass conservation. |
| G20 archive contains no secrets/credentials | PASS | Grep checks for `.env`, `secret`, `DS_Store` fail safely | `unzip -l ... \| grep -Ei 'secret'` | No private keys, passwords, or MacOS hidden files leaked into the artifact. |
