"""Fail-closed, real-data benchmark tooling for BubbleML operator models."""

from .data import CHANNEL_ALPHA, CHANNEL_TEMPERATURE, TensorSampleDataset
from .models import FNO2d, ModelSpec, UNet2d, build_model

__all__ = [
    "CHANNEL_ALPHA",
    "CHANNEL_TEMPERATURE",
    "FNO2d",
    "ModelSpec",
    "TensorSampleDataset",
    "UNet2d",
    "build_model",
]
