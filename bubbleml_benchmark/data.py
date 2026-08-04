"""BubbleML HDF5 to tensor conversion and validated tensor datasets.

The original BubbleML release stores ``temperature``, ``velx``, ``vely`` and
``dfun`` in every HDF5 simulation.  Some studies also store ``pressure``.
``pressure`` is a pressure *gradient*, not pressure.  ``dfun > 0`` denotes
vapor, so the alpha channel written here is a binary vapor mask derived from
the signed-distance field.  No synthetic data are ever generated.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import h5py
import numpy as np
import torch
from torch.nn import functional as F
from torch.utils.data import Dataset

CHANNEL_ALPHA = "alpha_vapor_mask"
CHANNEL_TEMPERATURE = "temperature"
REQUIRED_FIELDS = ("temperature", "velx", "vely", "dfun")


class DatasetValidationError(ValueError):
    """Raised when a real-data benchmark input does not meet the schema."""


@dataclass(frozen=True)
class PreprocessConfig:
    input_dir: str
    output_dir: str
    start_step: int = 30
    rollout_steps: int = 1
    stride: int = 1
    max_samples: int | None = None
    max_samples_per_source: int | None = None
    val_fraction: float = 0.15
    test_fraction: float = 0.15
    split_seed: int = 42
    nan_policy: Literal["error", "zero"] = "error"
    redimensionalize_temperature: bool = True
    target_resolution: int | None = None
    train_sources: tuple[str, ...] = ()
    val_sources: tuple[str, ...] = ()
    test_sources: tuple[str, ...] = ()


def _safe_torch_load(path: Path) -> dict[str, Any]:
    """Load only tensor/dict checkpoint-style data, never arbitrary pickles."""
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError as exc:  # pragma: no cover - project requires torch >= 2.2
        raise RuntimeError("BubbleML benchmark requires PyTorch >= 2.2.") from exc


def _finite_or_raise(array: np.ndarray, field: str, path: Path, policy: str) -> np.ndarray:
    if np.isfinite(array).all():
        return array
    if policy == "zero":
        return np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)
    invalid = int(np.size(array) - np.isfinite(array).sum())
    raise DatasetValidationError(
        f"{path}: {field} contains {invalid} NaN/Inf entries. "
        "Repair the interpolation or pass --nan-policy zero explicitly."
    )


def _temperature_scale(path: Path) -> float:
    """Match the official BubbleML v1 filename-based Twall re-dimensionalization."""
    match = re.search(r"(?:^|[_-])Twall[-_]?([0-9]+(?:\.[0-9]+)?)", path.stem, re.IGNORECASE)
    return float(match.group(1)) if match else 1.0


def _spacing_from_coordinate_grid(grid: np.ndarray, axis: int) -> float | None:
    """Infer a uniform grid spacing from an HxW (or TxHxW) coordinate field."""
    if grid.ndim == 3:
        grid = grid[0]
    if grid.ndim != 2:
        return None
    diffs = np.diff(grid, axis=axis)
    nonzero = np.abs(diffs[np.isfinite(diffs) & (np.abs(diffs) > 0)])
    if nonzero.size == 0:
        return None
    spacing = float(np.median(nonzero))
    if not math.isfinite(spacing) or spacing <= 0:
        return None
    return spacing


def _spatial_metadata(handle: h5py.File) -> tuple[float, float, str]:
    """Return dx, dy and whether they are physical coordinates or grid cells."""
    if "x" in handle and "y" in handle:
        # x varies across columns; y varies across rows.
        dx = _spacing_from_coordinate_grid(np.asarray(handle["x"][0]), axis=-1)
        dy = _spacing_from_coordinate_grid(np.asarray(handle["y"][0]), axis=-2)
        if dx is not None and dy is not None:
            return dx, dy, "coordinate_grid"
    # BubbleML 2.0 sample HDF5 files intentionally omit coordinate grids.
    return 1.0, 1.0, "grid_cells"


def _state_at(
    handle: h5py.File,
    index: int,
    source: Path,
    *,
    nan_policy: str,
    redimensionalize_temperature: bool,
    include_pressure_gradient: bool,
    target_resolution: int | None,
) -> np.ndarray:
    temperature = np.asarray(handle["temperature"][index], dtype=np.float32)
    if redimensionalize_temperature:
        temperature = temperature * _temperature_scale(source)
    fields = [
        np.asarray(handle["velx"][index], dtype=np.float32),
        np.asarray(handle["vely"][index], dtype=np.float32),
    ]
    if include_pressure_gradient:
        fields.append(np.asarray(handle["pressure"][index], dtype=np.float32))
    fields.extend(
        [
            temperature,
            (np.asarray(handle["dfun"][index], dtype=np.float32) > 0.0).astype(np.float32),
        ]
    )
    checked = [
        _finite_or_raise(field, name, source, nan_policy)
        for field, name in zip(
            fields,
            ("velx", "vely")
            + (("pressure",) if include_pressure_gradient else ())
            + ("temperature", "dfun"),
            strict=True,
        )
    ]
    shape = checked[0].shape
    if len(shape) != 2 or any(item.shape != shape for item in checked):
        raise DatasetValidationError(f"{source}: fields at time {index} do not share an HxW shape.")
    state = np.stack(checked, axis=0)
    if target_resolution is None:
        return state
    if target_resolution < 2 or target_resolution > min(shape):
        raise DatasetValidationError(
            f"{source}: target_resolution={target_resolution} must lie in [2, {min(shape)}]."
        )
    if shape == (target_resolution, target_resolution):
        return state
    values = torch.from_numpy(state).unsqueeze(0)
    continuous = F.interpolate(
        values[:, :-1],
        size=(target_resolution, target_resolution),
        mode="bilinear",
        align_corners=False,
    )
    alpha = F.interpolate(
        values[:, -1:],
        size=(target_resolution, target_resolution),
        mode="nearest",
    )
    return torch.cat((continuous, alpha), dim=1)[0].numpy()


def _trajectory_splits(
    sources: Sequence[Path], val_fraction: float, test_fraction: float, seed: int
) -> dict[Path, str]:
    if not 0 <= val_fraction < 1 or not 0 <= test_fraction < 1 or val_fraction + test_fraction >= 1:
        raise ValueError("val_fraction and test_fraction must be >= 0 and sum to less than 1.")
    shuffled = sorted(
        sources,
        key=lambda path: hashlib.sha256(f"{seed}:{path.resolve()}".encode()).hexdigest(),
    )
    count = len(shuffled)
    if count == 0:
        return {}
    n_test = round(count * test_fraction)
    n_val = round(count * val_fraction)
    # Preserve at least one training trajectory.  With two local smoke-test
    # trajectories, this naturally yields one train and one validation split.
    n_test = min(n_test, max(0, count - 1))
    n_val = min(n_val, max(0, count - n_test - 1))
    result: dict[Path, str] = {}
    for index, source in enumerate(shuffled):
        result[source] = "test" if index < n_test else "val" if index < n_test + n_val else "train"
    return result


def _explicit_trajectory_splits(
    sources: Sequence[Path],
    train_sources: Sequence[str],
    val_sources: Sequence[str],
    test_sources: Sequence[str],
) -> dict[Path, str]:
    """Resolve an auditable filename/stem split, allowing deliberate exclusions."""
    requested = {
        "train": tuple(train_sources),
        "val": tuple(val_sources),
        "test": tuple(test_sources),
    }
    if not any(requested.values()):
        return {}
    if not all(requested.values()):
        raise ValueError("Explicit splits require non-empty train_sources, val_sources, and test_sources.")
    lookup: dict[str, Path] = {}
    for source in sources:
        for key in (source.name, source.stem):
            if key in lookup and lookup[key] != source:
                raise DatasetValidationError(f"Ambiguous source identifier {key!r} below the input directory.")
            lookup[key] = source
    result: dict[Path, str] = {}
    for split, identifiers in requested.items():
        for identifier in identifiers:
            source = lookup.get(identifier)
            if source is None:
                raise DatasetValidationError(
                    f"Explicit {split} source {identifier!r} was not found; use an exact filename or stem."
                )
            previous = result.get(source)
            if previous is not None:
                raise DatasetValidationError(
                    f"{source.name} is assigned to both {previous!r} and {split!r}."
                )
            result[source] = split
    return result


def _atomic_torch_save(value: Mapping[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(dict(value), temporary)
    os.replace(temporary, destination)


def preprocess_hdf5(config: PreprocessConfig) -> dict[str, Any]:
    """Convert actual BubbleML HDF5 trajectories into safe, independently loadable tensors.

    A split is assigned by whole source trajectory, never by random timesteps,
    so adjacent frames cannot leak between train and test.  The output requires
    real HDF5 inputs and fails closed if none are supplied.
    """
    input_root = Path(config.input_dir).expanduser().resolve()
    output_root = Path(config.output_dir).expanduser().resolve()
    if config.rollout_steps < 1 or config.start_step < 0 or config.stride < 1:
        raise ValueError("start_step >= 0, rollout_steps >= 1, and stride >= 1 are required.")
    if config.max_samples is not None and config.max_samples < 1:
        raise ValueError("max_samples must be positive when supplied.")
    if config.max_samples_per_source is not None and config.max_samples_per_source < 1:
        raise ValueError("max_samples_per_source must be positive when supplied.")
    sources = sorted({*input_root.rglob("*.h5"), *input_root.rglob("*.hdf5")})
    if not sources:
        raise DatasetValidationError(f"No .h5 or .hdf5 files found below {input_root}.")

    split_for_source = _explicit_trajectory_splits(
        sources,
        config.train_sources,
        config.val_sources,
        config.test_sources,
    ) or _trajectory_splits(sources, config.val_fraction, config.test_fraction, config.split_seed)
    selected_sources = [source for source in sources if source in split_for_source]
    manifest: dict[str, Any] = {
        "format": "bubbleml-pt-v1",
        "preprocess": asdict(config),
        "source_files": [str(path) for path in selected_sources],
        "excluded_source_files": [str(path) for path in sources if path not in split_for_source],
        "split_unit": "trajectory",
        "samples": [],
        "channel_names": None,
        "notes": [
            "alpha_vapor_mask is derived from dfun > 0; it is not a CFD volume-fraction field.",
            "pressure_gradient is retained only when the source HDF5 contains pressure.",
            "BubbleML data excludes physical boundary cells; edge metrics are interior-edge proxies.",
        ],
    }
    written = 0
    for source_index, source in enumerate(selected_sources):
        source_written = 0
        with h5py.File(source, "r") as handle:
            missing = [field for field in REQUIRED_FIELDS if field not in handle]
            if missing:
                raise DatasetValidationError(f"{source}: missing required BubbleML datasets {missing}.")
            n_steps = int(handle["temperature"].shape[0])
            if any(int(handle[field].shape[0]) != n_steps for field in REQUIRED_FIELDS):
                raise DatasetValidationError(f"{source}: time dimension disagrees across required fields.")
            include_pressure_gradient = "pressure" in handle
            channel_names = ["u", "v"]
            if include_pressure_gradient:
                channel_names.append("pressure_gradient")
            channel_names.extend([CHANNEL_TEMPERATURE, CHANNEL_ALPHA])
            if manifest["channel_names"] is None:
                manifest["channel_names"] = channel_names
            elif manifest["channel_names"] != channel_names:
                raise DatasetValidationError(
                    "Mixed source schemas found (some trajectories have pressure and others do not). "
                    "Preprocess those studies separately to avoid fabricated channels."
                )
            dx, dy, spacing_kind = _spatial_metadata(handle)
            source_height, source_width = map(int, handle["temperature"].shape[-2:])
            if config.target_resolution is not None:
                dx *= source_width / config.target_resolution
                dy *= source_height / config.target_resolution
            stop = n_steps - config.rollout_steps
            if config.start_step >= stop:
                raise DatasetValidationError(
                    f"{source}: only {n_steps} frames; start_step={config.start_step} and "
                    f"rollout_steps={config.rollout_steps} leave no samples."
                )
            source_digest = hashlib.sha1(str(source.resolve()).encode()).hexdigest()[:10]
            for timestep in range(config.start_step, stop, config.stride):
                current = _state_at(
                    handle,
                    timestep,
                    source,
                    nan_policy=config.nan_policy,
                    redimensionalize_temperature=config.redimensionalize_temperature,
                    include_pressure_gradient=include_pressure_gradient,
                    target_resolution=config.target_resolution,
                )
                rollout = np.stack(
                    [
                        _state_at(
                            handle,
                            future,
                            source,
                            nan_policy=config.nan_policy,
                            redimensionalize_temperature=config.redimensionalize_temperature,
                            include_pressure_gradient=include_pressure_gradient,
                            target_resolution=config.target_resolution,
                        )
                        for future in range(timestep + 1, timestep + config.rollout_steps + 1)
                    ],
                    axis=0,
                )
                relative = Path(split_for_source[source]) / f"sim{source_index:04d}_{source_digest}_t{timestep:06d}.pt"
                payload = {
                    "input": torch.from_numpy(current),
                    "target": torch.from_numpy(rollout[0]),
                    "rollout_targets": torch.from_numpy(rollout),
                    "dx": float(dx),
                    "dy": float(dy),
                    "spacing_kind": spacing_kind,
                    "channel_names": channel_names,
                    "source": str(source),
                    "timestep": timestep,
                }
                _atomic_torch_save(payload, output_root / relative)
                manifest["samples"].append(
                    {
                        "path": str(relative),
                        "source": str(source),
                        "timestep": timestep,
                        "split": split_for_source[source],
                        "dx": float(dx),
                        "dy": float(dy),
                        "spacing_kind": spacing_kind,
                    }
                )
                written += 1
                source_written += 1
                if (
                    config.max_samples_per_source is not None
                    and source_written >= config.max_samples_per_source
                ):
                    break
                if config.max_samples is not None and written >= config.max_samples:
                    break
        if config.max_samples is not None and written >= config.max_samples:
            break
    if not written:
        raise DatasetValidationError("Preprocessing completed without writing a real sample.")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


class ChannelNormalizer:
    """Per-channel train-split standardization stored inside each checkpoint."""

    def __init__(self, mean: torch.Tensor, std: torch.Tensor, channel_names: Sequence[str]):
        self.mean = mean.detach().to(dtype=torch.float32, device="cpu")
        self.std = std.detach().to(dtype=torch.float32, device="cpu").clamp_min(1e-6)
        self.channel_names = tuple(channel_names)
        if self.mean.ndim != 1 or self.mean.shape != self.std.shape:
            raise ValueError("Normalizer mean and std must be one-dimensional and equally shaped.")
        if len(self.channel_names) != self.mean.numel():
            raise ValueError("Normalizer channel names do not match mean/std dimensionality.")

    @property
    def channels(self) -> int:
        return int(self.mean.numel())

    def _view(self, tensor: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if tensor.ndim == 3:
            shape = (self.channels, 1, 1)
        elif tensor.ndim == 4:
            shape = (1, self.channels, 1, 1)
        else:
            raise ValueError(f"Expected CxHxW or BxCxHxW tensor, got {tuple(tensor.shape)}.")
        return self.mean.to(tensor).view(shape), self.std.to(tensor).view(shape)

    def encode(self, tensor: torch.Tensor) -> torch.Tensor:
        mean, std = self._view(tensor)
        return (tensor - mean) / std

    def decode(self, tensor: torch.Tensor) -> torch.Tensor:
        mean, std = self._view(tensor)
        return tensor * std + mean

    def state_dict(self) -> dict[str, Any]:
        return {"mean": self.mean.tolist(), "std": self.std.tolist(), "channel_names": list(self.channel_names)}

    @classmethod
    def from_state_dict(cls, state: Mapping[str, Any]) -> ChannelNormalizer:
        return cls(
            torch.tensor(state["mean"], dtype=torch.float32),
            torch.tensor(state["std"], dtype=torch.float32),
            state["channel_names"],
        )

    @classmethod
    def fit(cls, dataset: TensorSampleDataset) -> ChannelNormalizer:
        if dataset.normalizer is not None:
            raise ValueError("Fit a normalizer from an unnormalized dataset.")
        total: torch.Tensor | None = None
        total_sq: torch.Tensor | None = None
        count = 0
        for index in range(len(dataset)):
            sample = dataset.raw_item(index)["input"].to(torch.float64)
            channel_sum = sample.sum(dim=(-2, -1))
            channel_sq = sample.square().sum(dim=(-2, -1))
            total = channel_sum if total is None else total + channel_sum
            total_sq = channel_sq if total_sq is None else total_sq + channel_sq
            count += sample.shape[-2] * sample.shape[-1]
        if total is None or total_sq is None or count == 0:
            raise DatasetValidationError("Cannot fit a normalizer to an empty dataset.")
        mean = total / count
        variance = (total_sq / count - mean.square()).clamp_min(1e-12)
        return cls(mean.float(), variance.sqrt().float(), dataset.channel_names)


class TensorSampleDataset(Dataset[dict[str, Any]]):
    """Dataset backed by preprocessed real ``.pt`` BubbleML samples only."""

    def __init__(
        self,
        root: str | Path,
        split: str | None = None,
        normalizer: ChannelNormalizer | None = None,
    ):
        self.root = Path(root).expanduser().resolve()
        self.split = split
        self.normalizer = normalizer
        manifest_path = self.root / "manifest.json"
        if not manifest_path.is_file():
            raise DatasetValidationError(
                f"{self.root} has no manifest.json. Run bubbleml_benchmark.prepare on real HDF5 data first."
            )
        self.manifest = json.loads(manifest_path.read_text())
        self.channel_names = tuple(self.manifest.get("channel_names") or ())
        if not self.channel_names:
            raise DatasetValidationError(f"{manifest_path} has no channel_names.")
        entries = self.manifest.get("samples", [])
        if split is not None:
            entries = [entry for entry in entries if entry.get("split") == split]
        self.entries = entries
        self.paths = [self.root / entry["path"] for entry in entries]
        absent = [path for path in self.paths if not path.is_file()]
        if absent:
            raise DatasetValidationError(f"Manifest references missing tensor sample: {absent[0]}")
        if not self.paths:
            scope = f" split '{split}'" if split else ""
            raise DatasetValidationError(f"No tensor samples found for{scope} in {self.root}.")
        if normalizer is not None and normalizer.channel_names != self.channel_names:
            raise DatasetValidationError("Checkpoint normalizer channel schema differs from dataset manifest.")

    def __len__(self) -> int:
        return len(self.paths)

    def raw_item(self, index: int) -> dict[str, Any]:
        payload = _safe_torch_load(self.paths[index])
        expected = (len(self.channel_names),)
        for key in ("input", "target", "rollout_targets"):
            if key not in payload or not isinstance(payload[key], torch.Tensor):
                raise DatasetValidationError(f"{self.paths[index]} is missing tensor key '{key}'.")
        if payload["input"].shape[:1] != expected or payload["target"].shape[:1] != expected:
            raise DatasetValidationError(f"{self.paths[index]} does not match manifest channel count.")
        if tuple(payload.get("channel_names", ())) != self.channel_names:
            raise DatasetValidationError(f"{self.paths[index]} channel names disagree with manifest.")
        return payload

    def __getitem__(self, index: int) -> dict[str, Any]:
        payload = self.raw_item(index)
        item: dict[str, Any] = {
            **{key: value for key, value in payload.items() if key not in {"input", "target", "rollout_targets"}},
            "input": payload["input"].float(),
            "target": payload["target"].float(),
            "rollout_targets": payload["rollout_targets"].float(),
        }
        if self.normalizer is not None:
            item["input"] = self.normalizer.encode(item["input"])
            item["target"] = self.normalizer.encode(item["target"])
            rollouts = item["rollout_targets"]
            item["rollout_targets"] = self.normalizer.encode(rollouts)
        return item


def channel_index(channel_names: Sequence[str], name: str) -> int:
    try:
        return list(channel_names).index(name)
    except ValueError as exc:
        raise DatasetValidationError(f"Dataset has no '{name}' channel. Available: {list(channel_names)}") from exc
