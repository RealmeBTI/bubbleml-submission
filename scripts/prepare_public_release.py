#!/usr/bin/env python3
"""Build the filtered public-release staging tree and its checksum manifest.

The local repository retains journal-facing and audit-history material.  This
script stages only the inspection/reproduction artifacts enumerated below; it
does not publish anything or infer a license, author, URL, or DOI.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = (
    "README.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "DATASET.md",
    "CHECKPOINT_MANIFEST.md",
    "CHECKSUMS.md",
    "BIBLIOGRAPHY_VERIFICATION.md",
    "ARTIFACT_GAPS.md",
    "REPRODUCIBILITY_SELFTEST.md",
    "REPRODUCIBILITY_STATUS.md",
    "PUBLICATION_FILE_MATRIX.csv",
    "FINAL_PUBLICATION_MATRIX.csv",
    "FINAL_RELEASE_SCORECARD.md",
    "RELEASE_FINAL_REPORT.md",
    "PUBLIC_RELEASE_TRANSFORM.md",
    "requirements.txt",
    "environment.yml",
    "pyproject.toml",
    "zenodo_metadata.json",
)
TREE_DIRS = (
    "bubbleml_benchmark",
    "scripts",
    "tests",
    "experiments",
    "benchmark_results",
    "reproduced",
)
MANUSCRIPT_FILES = (
    "full_manuscript.md",
    "manuscript_elsarticle.tex",
    "elsarticle_template.tex",
    "references.bib",
)
SUPPLEMENTARY_FILES = (
    "statistical_audit_note.md",
    "runtime_environment.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def checksum_lines(stage: Path) -> list[str]:
    paths = sorted(path for path in stage.rglob("*") if path.is_file() and path.name != "RELEASE_SHA256SUMS.txt")
    return [f"{sha256(path)}  {path.relative_to(stage).as_posix()}" for path in paths]


def redact_private_paths(stage: Path) -> None:
    """Replace incidental local absolute paths in public text artifacts only."""
    extensions = {".json", ".yaml", ".yml", ".md", ".py", ".txt", ".tex", ".cff"}
    pattern = re.compile(r"/(?:Users|home|private|tmp|var)/[^\s\"']+")
    for path in stage.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        text = path.read_text(encoding="utf-8")
        redacted = pattern.sub("<local-path-redacted>", text)
        if redacted != text:
            path.write_text(redacted, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "public_release")
    args = parser.parse_args()
    stage = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    for relative in ROOT_FILES:
        copy_file(ROOT / relative, stage / relative)
    for relative in TREE_DIRS:
        shutil.copytree(
            ROOT / relative,
            stage / relative,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", ".pytest_cache", ".ruff_cache"),
        )
    for relative in MANUSCRIPT_FILES:
        copy_file(ROOT / "manuscript" / relative, stage / "manuscript" / relative)
    for relative in SUPPLEMENTARY_FILES:
        copy_file(ROOT / "submission" / "supplementary" / relative, stage / "submission" / "supplementary" / relative)
    shutil.copytree(ROOT / "submission" / "figures", stage / "submission" / "figures", ignore=shutil.ignore_patterns(".DS_Store"))
    redact_private_paths(stage)

    manifest = "\n".join(checksum_lines(stage)) + "\n"
    (stage / "RELEASE_SHA256SUMS.txt").write_text(manifest, encoding="utf-8")
    (ROOT / "RELEASE_SHA256SUMS.txt").write_text(manifest, encoding="utf-8")
    print(stage)


if __name__ == "__main__":
    main()
