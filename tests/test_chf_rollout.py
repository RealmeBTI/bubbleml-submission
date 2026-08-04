from __future__ import annotations

import pytest
import torch

from bubbleml_benchmark.chf_rollout import (
    _autoregressive_rollout,
    dry_area_fraction,
    first_sustained_crossing,
    protocol_event_threshold,
)
from bubbleml_benchmark.data import ChannelNormalizer


class IncrementModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[torch.Tensor] = []

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        self.inputs.append(inputs.detach().clone())
        return inputs + 1


def test_dry_area_fraction_uses_bottom_rows_and_strict_alpha_threshold() -> None:
    frames = torch.zeros(2, 3, 4, 5)
    frames[0, 2, 0, :3] = torch.tensor([0.5, 0.6, 1.0])
    frames[1, 2, :2] = 1.0
    frames[1, 2, 2:] = 1.0  # Must be excluded from the two-row heater region.

    result = dry_area_fraction(frames, alpha_index=2, heater_rows=2, alpha_threshold=0.5)

    assert result.tolist() == pytest.approx([0.2, 1.0])


def test_protocol_event_threshold_is_baseline_relative_with_minimum() -> None:
    signal = torch.tensor([0.04, 0.06, 0.05, 0.20])

    baseline, threshold = protocol_event_threshold(signal, 3, 0.10, 0.10)

    assert baseline == pytest.approx(0.05)
    assert threshold == pytest.approx(0.15)


def test_first_sustained_crossing_rejects_single_frame_spike() -> None:
    signal = torch.tensor([0.1, 0.4, 0.1, 0.4, 0.5, 0.6, 0.1])

    assert first_sustained_crossing(signal, threshold=0.3, sustain_frames=3) == 3
    assert first_sustained_crossing(signal, threshold=0.7, sustain_frames=2) is None


def test_rollout_feeds_predictions_back_without_ground_truth() -> None:
    model = IncrementModel()
    normalizer = ChannelNormalizer(torch.zeros(1), torch.ones(1), ("alpha_vapor_mask",))
    history = torch.tensor([[[[1.0]]], [[[2.0]]]])

    prediction = _autoregressive_rollout(
        model,
        normalizer,
        torch.device("cpu"),
        history,
        steps=3,
        future_size=2,
    )

    assert prediction.flatten().tolist() == pytest.approx([2.0, 3.0, 3.0])
    assert len(model.inputs) == 2
    assert torch.equal(model.inputs[1], model.inputs[0] + 1)
