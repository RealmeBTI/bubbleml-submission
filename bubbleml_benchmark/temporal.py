"""Leakage-safe temporal bundles over preprocessed five-field BubbleML states."""

from __future__ import annotations

from collections import defaultdict
from itertools import pairwise
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import Dataset

from .data import ChannelNormalizer, DatasetValidationError, TensorSampleDataset


class TemporalBundleDataset(Dataset[dict[str, Any]]):
    """Build history/future windows without crossing trajectory boundaries.

    The underlying preprocessor stores one physical state per timestep. This
    wrapper groups adjacent entries from the same source trajectory, applies a
    single-frame train-split normalizer to every frame, and flattens time into
    the channel dimension expected by 2-D image-to-image models.
    """

    def __init__(
        self,
        root: str | Path,
        split: str,
        normalizer: ChannelNormalizer,
        *,
        history_size: int = 5,
        future_size: int = 5,
        rollout_bundles: int = 1,
        cache_frames: bool = False,
    ):
        if min(history_size, future_size, rollout_bundles) < 1:
            raise ValueError("history_size, future_size, and rollout_bundles must be positive.")
        self.base = TensorSampleDataset(root, split=split)
        if normalizer.channel_names != self.base.channel_names:
            raise DatasetValidationError("Temporal normalizer schema differs from the dataset schema.")
        self.normalizer = normalizer
        self.history_size = history_size
        self.future_size = future_size
        self.rollout_bundles = rollout_bundles
        self.channel_names = self.base.channel_names
        self.channels = len(self.channel_names)
        self.in_channels = self.channels * history_size
        self.out_channels = self.channels * future_size

        trajectories: dict[str, list[int]] = defaultdict(list)
        for index, entry in enumerate(self.base.entries):
            trajectories[str(entry["source"])].append(index)
        for indices in trajectories.values():
            indices.sort(key=lambda index: int(self.base.entries[index]["timestep"]))

        required_future = future_size * rollout_bundles
        self.windows: list[tuple[int, ...]] = []
        for indices in trajectories.values():
            stop = len(indices) - history_size - required_future + 1
            for start in range(max(0, stop)):
                window = tuple(indices[start : start + history_size + required_future])
                timesteps = [int(self.base.entries[index]["timestep"]) for index in window]
                increments = {right - left for left, right in pairwise(timesteps)}
                if increments == {1}:
                    self.windows.append(window)
        if not self.windows:
            raise DatasetValidationError(
                f"Split {split!r} has no contiguous history={history_size}, future={future_size}, "
                f"rollout_bundles={rollout_bundles} windows."
            )
        self._encoded_cache: dict[int, torch.Tensor] = {}
        if cache_frames:
            used_indices = sorted({item for window in self.windows for item in window})
            self._encoded_cache = {
                item: self.normalizer.encode(self.base.raw_item(item)["input"].float())
                for item in used_indices
            }

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        indices = self.windows[index]
        encoded = torch.stack(
            [
                self._encoded_cache[item]
                if item in self._encoded_cache
                else self.normalizer.encode(self.base.raw_item(item)["input"].float())
                for item in indices
            ]
        )
        history = encoded[: self.history_size]
        future = encoded[self.history_size :]
        bundles = future.view(
            self.rollout_bundles,
            self.future_size,
            self.channels,
            *future.shape[-2:],
        )
        anchor = self.base.entries[indices[self.history_size - 1]]
        return {
            "input": history.flatten(0, 1),
            "target": bundles[0].flatten(0, 1),
            "rollout_targets": bundles.flatten(1, 2),
            "dx": float(anchor["dx"]),
            "dy": float(anchor["dy"]),
            "spacing_kind": anchor.get("spacing_kind", "unknown"),
            "source": anchor["source"],
            "timestep": int(anchor["timestep"]),
        }

    def decode_frames(self, tensor: torch.Tensor, frames: int) -> torch.Tensor:
        """Decode flattened temporal channels to ``... x T x C x H x W``."""
        if tensor.shape[-3] != frames * self.channels:
            raise ValueError(
                f"Expected {frames * self.channels} flattened channels, got {tensor.shape[-3]}."
            )
        prefix = tensor.shape[:-3]
        shaped = tensor.view(*prefix, frames, self.channels, *tensor.shape[-2:])
        flattened = shaped.flatten(0, -4)
        decoded = self.normalizer.decode(flattened)
        return decoded.view(*prefix, frames, self.channels, *tensor.shape[-2:])
