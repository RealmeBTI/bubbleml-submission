"""Shape-safe vanilla FNO and U-Net baselines used by the BubbleML benchmark."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Literal

import torch
from torch import nn
from torch.nn import functional as F


@dataclass(frozen=True)
class ModelSpec:
    kind: Literal["fno", "unet"]
    in_channels: int
    out_channels: int
    fno_modes: tuple[int, int] = (12, 12)
    fno_width: int = 32
    fno_layers: int = 4
    fno_padding: int = 8
    unet_features: int = 32
    unet_depth: int = 4

    def state_dict(self) -> dict[str, object]:
        state = asdict(self)
        state["fno_modes"] = list(self.fno_modes)
        return state

    @classmethod
    def from_state_dict(cls, state: Mapping[str, object]) -> ModelSpec:
        value = dict(state)
        value["fno_modes"] = tuple(value["fno_modes"])
        return cls(**value)  # type: ignore[arg-type]


class SpectralConv2d(nn.Module):
    """A standard low-frequency Fourier layer with safe mode truncation."""

    def __init__(self, in_channels: int, out_channels: int, modes1: int, modes2: int):
        super().__init__()
        if min(in_channels, out_channels, modes1, modes2) < 1:
            raise ValueError("SpectralConv2d channels and modes must be positive.")
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = modes1
        self.modes2 = modes2
        scale = 1.0 / math.sqrt(in_channels * out_channels)
        self.weights_positive = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.cfloat)
        )
        self.weights_negative = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.cfloat)
        )

    @staticmethod
    def _complex_multiply(inputs: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
        return torch.einsum("bixy,ioxy->boxy", inputs, weights)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 4:
            raise ValueError(f"SpectralConv2d expects BxCxHxW, got {tuple(inputs.shape)}.")
        height, width = inputs.shape[-2:]
        transformed = torch.fft.rfft2(inputs, norm="ortho")
        output = transformed.new_zeros(inputs.shape[0], self.out_channels, height, width // 2 + 1)
        # Limiting vertical modes to half the height prevents the positive and
        # negative blocks overlapping on small/downsampled real-data grids.
        modes1 = min(self.modes1, height // 2)
        modes2 = min(self.modes2, width // 2 + 1)
        if modes1 and modes2:
            output[:, :, :modes1, :modes2] = self._complex_multiply(
                transformed[:, :, :modes1, :modes2], self.weights_positive[:, :, :modes1, :modes2]
            )
            output[:, :, -modes1:, :modes2] = self._complex_multiply(
                transformed[:, :, -modes1:, :modes2], self.weights_negative[:, :, :modes1, :modes2]
            )
        return torch.fft.irfft2(output, s=(height, width), norm="ortho")


class FNO2d(nn.Module):
    """Vanilla FNO with coordinate lifting and one-sided wall padding."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        modes: tuple[int, int] = (12, 12),
        width: int = 32,
        layers: int = 4,
        padding: int = 8,
    ):
        super().__init__()
        if layers < 1 or width < 1 or padding < 0:
            raise ValueError("FNO width/layers must be positive and padding must be non-negative.")
        self.padding = padding
        self.lift = nn.Linear(in_channels + 2, width)
        self.spectral_layers = nn.ModuleList(
            [SpectralConv2d(width, width, *modes) for _ in range(layers)]
        )
        self.pointwise_layers = nn.ModuleList([nn.Conv2d(width, width, kernel_size=1) for _ in range(layers)])
        self.projection1 = nn.Linear(width, max(128, width * 2))
        self.projection2 = nn.Linear(max(128, width * 2), out_channels)

    @staticmethod
    def _coordinate_grid(inputs: torch.Tensor) -> torch.Tensor:
        batch, _, height, width = inputs.shape
        x = torch.linspace(0.0, 1.0, height, device=inputs.device, dtype=inputs.dtype)
        y = torch.linspace(0.0, 1.0, width, device=inputs.device, dtype=inputs.dtype)
        grid_x = x.view(1, 1, height, 1).expand(batch, 1, height, width)
        grid_y = y.view(1, 1, 1, width).expand(batch, 1, height, width)
        return torch.cat((grid_x, grid_y), dim=1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 4:
            raise ValueError(f"FNO2d expects BxCxHxW, got {tuple(inputs.shape)}.")
        original_height, original_width = inputs.shape[-2:]
        if self.padding:
            inputs = F.pad(inputs, (0, self.padding, 0, self.padding), mode="replicate")
        features = torch.cat((inputs, self._coordinate_grid(inputs)), dim=1).permute(0, 2, 3, 1)
        features = self.lift(features).permute(0, 3, 1, 2)
        for spectral, pointwise in zip(self.spectral_layers, self.pointwise_layers, strict=True):
            features = F.gelu(spectral(features) + pointwise(features))
        features = features.permute(0, 2, 3, 1)
        outputs = self.projection2(F.gelu(self.projection1(features))).permute(0, 3, 1, 2)
        return outputs[..., :original_height, :original_width]


def _group_count(channels: int) -> int:
    for candidate in range(min(8, channels), 0, -1):
        if channels % candidate == 0:
            return candidate
    return 1


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(out_channels), out_channels),
            nn.GELU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(out_channels), out_channels),
            nn.GELU(),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.layers(inputs)


class UNet2d(nn.Module):
    """U-Net that preserves any HxW input via replicate padding and exact resize."""

    def __init__(self, in_channels: int, out_channels: int, features: int = 32, depth: int = 4):
        super().__init__()
        if features < 1 or depth < 1:
            raise ValueError("U-Net features and depth must be positive.")
        widths = [features * (2**level) for level in range(depth)]
        self.factor = 2**depth
        self.down_blocks = nn.ModuleList()
        current = in_channels
        for width in widths:
            self.down_blocks.append(ConvBlock(current, width))
            current = width
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = ConvBlock(widths[-1], widths[-1] * 2)
        self.up_transpose = nn.ModuleList()
        self.up_blocks = nn.ModuleList()
        current = widths[-1] * 2
        for width in reversed(widths):
            self.up_transpose.append(nn.ConvTranspose2d(current, width, kernel_size=2, stride=2))
            self.up_blocks.append(ConvBlock(width * 2, width))
            current = width
        self.final = nn.Conv2d(widths[0], out_channels, kernel_size=1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 4:
            raise ValueError(f"UNet2d expects BxCxHxW, got {tuple(inputs.shape)}.")
        original_height, original_width = inputs.shape[-2:]
        pad_h = (self.factor - original_height % self.factor) % self.factor
        pad_w = (self.factor - original_width % self.factor) % self.factor
        if pad_h or pad_w:
            inputs = F.pad(inputs, (0, pad_w, 0, pad_h), mode="replicate")
        skips = []
        features = inputs
        for block in self.down_blocks:
            features = block(features)
            skips.append(features)
            features = self.pool(features)
        features = self.bottleneck(features)
        for transpose, block, skip in zip(self.up_transpose, self.up_blocks, reversed(skips), strict=True):
            features = transpose(features)
            # ConvTranspose can differ by one cell on non-power-of-two grids.
            # Resize the decoder branch rather than cropping a skip connection.
            if features.shape[-2:] != skip.shape[-2:]:
                features = F.interpolate(features, size=skip.shape[-2:], mode="bilinear", align_corners=False)
            features = block(torch.cat((skip, features), dim=1))
        return self.final(features)[..., :original_height, :original_width]


def build_model(spec: ModelSpec) -> nn.Module:
    if spec.kind == "fno":
        return FNO2d(
            spec.in_channels,
            spec.out_channels,
            modes=spec.fno_modes,
            width=spec.fno_width,
            layers=spec.fno_layers,
            padding=spec.fno_padding,
        )
    if spec.kind == "unet":
        return UNet2d(spec.in_channels, spec.out_channels, spec.unet_features, spec.unet_depth)
    raise ValueError(f"Unknown model kind: {spec.kind}")
