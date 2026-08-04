"""Explicit downloader for the official BubbleML 1.0 study archives.

The original release distributes one tarball per study.  ``--max-trajectories``
limits extraction and disk use, but cannot avoid downloading the selected
archive because the public source does not expose individual HDF5 objects.
"""

from __future__ import annotations

import argparse
import shutil
import tarfile
import urllib.request
from pathlib import Path

STUDY_URLS = {
    "single-bubble": "https://bubble-ml-simulations.s3.us-east-2.amazonaws.com/single-bubble.tar.gz",
    "pool-boiling-saturated": "https://bubble-ml-simulations.s3.us-east-2.amazonaws.com/pool-boiling-saturated-fc72-2d.tar.gz",
    "pool-boiling-subcooled": "https://bubble-ml-simulations.s3.us-east-2.amazonaws.com/pool-boiling-subcooled-fc72-2d.tar.gz",
    "flow-boiling-velocity": "https://bubble-ml-simulations.s3.us-east-2.amazonaws.com/flow-boiling-velscale-fc72-2d.tar.gz",
}


def _safe_member_name(member: tarfile.TarInfo) -> Path:
    name = Path(member.name)
    if name.is_absolute() or ".." in name.parts:
        raise ValueError(f"Unsafe path inside archive: {member.name}")
    return name


def _download_with_resume(url: str, temporary: Path) -> None:
    """Resume an interrupted public archive transfer when the S3 endpoint supports Range."""
    offset = temporary.stat().st_size if temporary.exists() else 0
    request = urllib.request.Request(url)
    if offset:
        request.add_header("Range", f"bytes={offset}-")
        print(f"Resuming official archive at byte {offset:,}")
    with urllib.request.urlopen(request, timeout=60) as response:
        partial_response = getattr(response, "status", None) == 206
        mode = "ab" if offset and partial_response else "wb"
        if offset and not partial_response:
            print("Server did not honor Range; restarting archive download.")
        with temporary.open(mode) as target:
            shutil.copyfileobj(response, target, length=1024 * 1024)


def download_and_extract(study: str, archive_dir: str | Path, output_dir: str | Path, max_trajectories: int) -> list[Path]:
    if study not in STUDY_URLS:
        raise ValueError(f"Unknown study '{study}'.")
    if max_trajectories < 1:
        raise ValueError("max_trajectories must be positive.")
    archive_dir = Path(archive_dir).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    archive_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / f"{study}.tar.gz"
    temporary = archive.with_suffix(archive.suffix + ".part")
    if archive.exists() and archive.stat().st_size == 0:
        archive.unlink()
    if not archive.exists():
        print(f"Downloading official {study} archive to {archive}")
        _download_with_resume(STUDY_URLS[study], temporary)
        temporary.replace(archive)
    extracted: list[Path] = []
    with tarfile.open(archive, mode="r:gz") as tar:
        candidates = [member for member in tar if member.isfile() and member.name.lower().endswith((".h5", ".hdf5"))]
        if not candidates:
            raise ValueError(f"{archive} contains no HDF5 trajectories.")
        for member in candidates[:max_trajectories]:
            destination = output_dir / _safe_member_name(member).name
            with tar.extractfile(member) as source, destination.open("wb") as target:
                if source is None:
                    raise ValueError(f"Cannot extract {member.name} from {archive}")
                shutil.copyfileobj(source, target)
            extracted.append(destination)
    return extracted


def main() -> None:
    parser = argparse.ArgumentParser(description="Download one official BubbleML study and extract a small real HDF5 subset.")
    parser.add_argument("--study", required=True, choices=tuple(STUDY_URLS))
    parser.add_argument("--archive-dir", default="data/bubbleml/archives")
    parser.add_argument("--output-dir", default="data/bubbleml/hdf5")
    parser.add_argument("--max-trajectories", type=int, default=2)
    args = parser.parse_args()
    files = download_and_extract(args.study, args.archive_dir, args.output_dir, args.max_trajectories)
    print("Extracted real HDF5 trajectories:")
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
