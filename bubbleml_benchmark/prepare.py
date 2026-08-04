"""CLI for converting official BubbleML HDF5 trajectories into .pt samples."""

from __future__ import annotations

import argparse
from pathlib import Path

from .data import PreprocessConfig, preprocess_hdf5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert real BubbleML HDF5 trajectories to validated .pt samples.")
    parser.add_argument("--input-dir", required=True, help="Directory containing official .h5/.hdf5 trajectories.")
    parser.add_argument("--output-dir", required=True, help="Destination for train/val/test .pt samples and manifest.")
    parser.add_argument("--start-step", type=int, default=30, help="Discard unsteady initial frames (official v1 guidance).")
    parser.add_argument("--rollout-steps", type=int, default=1, help="Store this many future ground-truth frames per sample.")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=None, help="Cap output for a local smoke test.")
    parser.add_argument(
        "--max-samples-per-source",
        type=int,
        default=None,
        help="Cap each trajectory equally; intended for balanced native-resolution checks.",
    )
    parser.add_argument("--val-fraction", type=float, default=0.15)
    parser.add_argument("--test-fraction", type=float, default=0.15)
    parser.add_argument("--split-seed", type=int, default=42)
    parser.add_argument("--nan-policy", choices=("error", "zero"), default="error")
    parser.add_argument("--no-redimensionalize-temperature", action="store_true")
    parser.add_argument(
        "--target-resolution",
        type=int,
        default=None,
        help="Optionally downsample every HDF5 field to a square resolution (alpha uses nearest-neighbor).",
    )
    parser.add_argument("--train-sources", default="", help="Comma-separated exact HDF5 filenames or stems.")
    parser.add_argument("--val-sources", default="", help="Comma-separated exact HDF5 filenames or stems.")
    parser.add_argument("--test-sources", default="", help="Comma-separated exact HDF5 filenames or stems.")
    return parser


def _csv_strings(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def main() -> None:
    args = build_parser().parse_args()
    manifest = preprocess_hdf5(
        PreprocessConfig(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            start_step=args.start_step,
            rollout_steps=args.rollout_steps,
            stride=args.stride,
            max_samples=args.max_samples,
            max_samples_per_source=args.max_samples_per_source,
            val_fraction=args.val_fraction,
            test_fraction=args.test_fraction,
            split_seed=args.split_seed,
            nan_policy=args.nan_policy,
            redimensionalize_temperature=not args.no_redimensionalize_temperature,
            target_resolution=args.target_resolution,
            train_sources=_csv_strings(args.train_sources),
            val_sources=_csv_strings(args.val_sources),
            test_sources=_csv_strings(args.test_sources),
        )
    )
    counts = {split: sum(item["split"] == split for item in manifest["samples"]) for split in ("train", "val", "test")}
    print(f"Wrote {len(manifest['samples'])} real samples to {Path(args.output_dir).resolve()}")
    print(f"Channels: {manifest['channel_names']}; splits: {counts}")


if __name__ == "__main__":
    main()
