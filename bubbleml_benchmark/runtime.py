"""Reproducibility and safe device selection, including the MPS/FNO probe."""

from __future__ import annotations

import random
from typing import Literal

import numpy as np
import torch

from .models import ModelSpec, build_model


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def available_device(requested: str = "auto") -> torch.device:
    if requested == "auto":
        requested = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable.")
    if device.type == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS was requested but is unavailable.")
    return device


def fno_device(requested: str, spec: ModelSpec, sample_shape: tuple[int, int] = (32, 32)) -> torch.device:
    """Use MPS only if its complex FFT forward/backward path actually works."""
    device = available_device(requested)
    if device.type != "mps":
        return device
    height, width = sample_shape
    try:
        # The evaluator is inference-decorated, but the compatibility probe
        # must exercise the complex backward path as well as the forward FFT.
        with torch.inference_mode(False), torch.enable_grad():
            model = build_model(spec).to(device).train()
            inputs = torch.zeros(1, spec.in_channels, height, width, device=device)
            model(inputs).square().mean().backward()
            torch.mps.synchronize()
            del model, inputs
        return device
    except (NotImplementedError, RuntimeError) as exc:
        print(f"[WARN] MPS complex FFT probe failed for FNO ({exc}). Falling back to CPU for FNO.")
        return torch.device("cpu")


def synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elif device.type == "mps":
        torch.mps.synchronize()


def autocast_enabled(device: torch.device, requested: bool, model_kind: Literal["fno", "unet"]) -> bool:
    """Keep Fourier FFT/complex math in fp32; use AMP only for CUDA U-Net runs."""
    return bool(requested and device.type == "cuda" and model_kind == "unet")


def device_autocast(device: torch.device, enabled: bool):
    return torch.autocast(device_type=device.type, enabled=enabled)
