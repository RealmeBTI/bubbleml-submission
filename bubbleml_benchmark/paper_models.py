"""Paper-oriented FNO, Tucker FNO, factorized FNO, and U-Net models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Literal

import torch
from neuralop.models import FNO as NeuralOpFNO
from torch import nn
from torch.nn import functional as F

from .models import UNet2d

PaperModelKind = Literal["fno", "tfno", "hybrid_tfno", "hybrid_div", "ffno", "unet"]


@dataclass(frozen=True)
class PaperModelSpec:
    kind: PaperModelKind
    in_channels: int
    out_channels: int
    requested_modes: tuple[int, int] = (24, 24)
    effective_modes: tuple[int, int] = (24, 24)
    width: int = 64
    layers: int = 4
    domain_padding: float = 0.1
    tfno_rank: float = 0.1
    unet_features: int = 32
    unet_depth: int = 4
    alpha_bounded: bool = False
    alpha_output_indices: tuple[int, ...] = ()
    alpha_normalized_lower: float | None = None
    alpha_normalized_upper: float | None = None

    def state_dict(self) -> dict[str, object]:
        state = asdict(self)
        state["requested_modes"] = list(self.requested_modes)
        state["effective_modes"] = list(self.effective_modes)
        state["alpha_output_indices"] = list(self.alpha_output_indices)
        return state

    @classmethod
    def from_state_dict(cls, state: Mapping[str, object]) -> PaperModelSpec:
        value = dict(state)
        value["requested_modes"] = tuple(value["requested_modes"])
        value["effective_modes"] = tuple(value["effective_modes"])
        value["alpha_output_indices"] = tuple(value.get("alpha_output_indices", ()))
        return cls(**value)  # type: ignore[arg-type]


class BoundedAlphaOutput(nn.Module):
    """Constrain only encoded alpha outputs to the physical [0, 1] interval.

    Training targets are channel-standardized.  Mapping a sigmoid through the
    encoded values of physical zero and one preserves an actual physical bound
    after ``ChannelNormalizer.decode`` while leaving every non-alpha output
    untouched.
    """

    def __init__(
        self,
        model: nn.Module,
        alpha_output_indices: tuple[int, ...],
        normalized_lower: float,
        normalized_upper: float,
    ):
        super().__init__()
        if not alpha_output_indices:
            raise ValueError("A bounded-alpha model requires at least one alpha output channel.")
        if normalized_upper <= normalized_lower:
            raise ValueError("Encoded alpha bounds must be strictly increasing.")
        self.model = model
        self.alpha_output_indices = alpha_output_indices
        self.normalized_lower = normalized_lower
        self.normalized_upper = normalized_upper

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        output = self.model(inputs)
        bounded = output.clone()
        alpha = output[:, self.alpha_output_indices]
        bounded[:, self.alpha_output_indices] = self.normalized_lower + (
            self.normalized_upper - self.normalized_lower
        ) * torch.sigmoid(alpha)
        return bounded


class AxisFactorizedSpectralConv2d(nn.Module):
    """F-FNO spectral convolution factorized over the two spatial axes."""

    def __init__(self, channels: int, modes: int):
        super().__init__()
        scale = 1.0 / max(1, channels)
        self.modes = modes
        self.weight_x = nn.Parameter(
            scale * torch.randn(channels, channels, modes, dtype=torch.cfloat)
        )
        self.weight_y = nn.Parameter(
            scale * torch.randn(channels, channels, modes, dtype=torch.cfloat)
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        batch, _, height, width = inputs.shape
        modes_x = min(self.modes, height // 2 + 1)
        modes_y = min(self.modes, width // 2 + 1)

        transformed_y = torch.fft.rfft(inputs, dim=-1, norm="ortho")
        output_y = transformed_y.new_zeros(batch, inputs.shape[1], height, width // 2 + 1)
        output_y[..., :modes_y] = torch.einsum(
            "bihm,iom->bohm",
            transformed_y[..., :modes_y],
            self.weight_y[..., :modes_y],
        )
        spatial_y = torch.fft.irfft(output_y, n=width, dim=-1, norm="ortho")

        transformed_x = torch.fft.rfft(inputs, dim=-2, norm="ortho")
        output_x = transformed_x.new_zeros(batch, inputs.shape[1], height // 2 + 1, width)
        output_x[:, :, :modes_x, :] = torch.einsum(
            "bimw,iom->bomw",
            transformed_x[:, :, :modes_x, :],
            self.weight_x[..., :modes_x],
        )
        spatial_x = torch.fft.irfft(output_x, n=height, dim=-2, norm="ortho")
        return spatial_x + spatial_y


class FFNOBlock(nn.Module):
    def __init__(self, width: int, modes: int, dropout: float = 0.0):
        super().__init__()
        self.spectral = AxisFactorizedSpectralConv2d(width, modes)
        self.norm = nn.LayerNorm(width)
        self.feedforward = nn.Sequential(
            nn.Conv2d(width, width * 2, 1),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Conv2d(width * 2, width, 1),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        features = self.spectral(inputs)
        features = self.norm(features.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        return self.feedforward(features)


class FFNO2d(nn.Module):
    """BubbleML-style Factorized FNO with post-nonlinearity residuals."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        modes: int,
        width: int,
        layers: int,
        domain_padding: float = 0.1,
    ):
        super().__init__()
        self.domain_padding = domain_padding
        self.input_projection = nn.Conv2d(in_channels + 2, width, 1)
        self.blocks = nn.ModuleList([FFNOBlock(width, modes) for _ in range(layers)])
        self.output_projection = nn.Sequential(
            nn.Conv2d(width, 128, 1),
            nn.GELU(),
            nn.Conv2d(128, out_channels, 1),
        )

    @staticmethod
    def _grid(inputs: torch.Tensor) -> torch.Tensor:
        batch, _, height, width = inputs.shape
        y = torch.linspace(0, 1, height, device=inputs.device, dtype=inputs.dtype)
        x = torch.linspace(0, 1, width, device=inputs.device, dtype=inputs.dtype)
        return torch.stack(torch.meshgrid(y, x, indexing="ij"), dim=0).expand(batch, -1, -1, -1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        height, width = inputs.shape[-2:]
        pad_h = round(height * self.domain_padding)
        pad_w = round(width * self.domain_padding)
        if pad_h or pad_w:
            inputs = F.pad(inputs, (0, pad_w, 0, pad_h))
        features = self.input_projection(torch.cat((inputs, self._grid(inputs)), dim=1))
        backcast = features
        for block in self.blocks:
            backcast = block(features)
            features = features + backcast
        return self.output_projection(backcast)[..., :height, :width]


class LocalResidualFNOBlocks(nn.Module):
    """Add a local 3x3 branch to each post-activation T-FNO block.

    NeuralOperator's block already computes the Tucker spectral branch and the
    learned linear skip ``W x``.  This adapter inserts ``Conv3x3(x)`` into that
    same pre-activation sum, yielding

        spectral_TFNO(x) + Conv3x3(x) + W x.

    The channel MLP, normalization, activation, and spectral implementation are
    otherwise identical to the paper T-FNO baseline.
    """

    def __init__(self, blocks: nn.Module, channels: int, layers: int):
        super().__init__()
        if getattr(blocks, "preactivation", False):
            raise ValueError("The local T-FNO adapter requires post-activation FNO blocks.")
        if getattr(blocks, "complex_data", False):
            raise ValueError("The local T-FNO adapter supports real-valued fields only.")
        self.blocks = blocks
        self.local_convs = nn.ModuleList(
            [nn.Conv2d(channels, channels, kernel_size=3, padding=1) for _ in range(layers)]
        )

    def forward(
        self, inputs: torch.Tensor, index: int = 0, output_shape: tuple[int, int] | None = None
    ) -> torch.Tensor:
        blocks = self.blocks
        if blocks.fno_skips is not None:
            skip = blocks.fno_skips[index](inputs)
            skip = blocks.convs[index].transform(skip, output_shape=output_shape)

        if blocks.use_channel_mlp and blocks.channel_mlp_skips is not None:
            channel_skip = blocks.channel_mlp_skips[index](inputs)
            channel_skip = blocks.convs[index].transform(
                channel_skip, output_shape=output_shape
            )

        stabilized = torch.tanh(inputs) if blocks.stabilizer == "tanh" else inputs
        spectral = blocks.convs[index](stabilized, output_shape=output_shape)
        if blocks.norm is not None:
            spectral = blocks.norm[blocks.n_norms * index](spectral)

        local = self.local_convs[index](inputs)
        local = blocks.convs[index].transform(local, output_shape=output_shape)
        output = spectral + local
        if blocks.fno_skips is not None:
            output = output + skip

        if index < blocks.n_layers - 1:
            output = blocks.non_linearity(output)

        if blocks.use_channel_mlp:
            output = blocks.channel_mlp[index](output)
            if blocks.channel_mlp_skips is not None:
                output = output + channel_skip

        if blocks.norm is not None:
            output = blocks.norm[blocks.n_norms * index + 1](output)
        if index < blocks.n_layers - 1:
            output = blocks.non_linearity(output)
        return output


class HybridTFNO2d(NeuralOpFNO):
    """Tucker FNO with a trainable local 3x3 branch at every spectral layer."""

    def __init__(self, **kwargs: object):
        super().__init__(**kwargs)
        self.fno_blocks = LocalResidualFNOBlocks(
            self.fno_blocks, int(self.hidden_channels), int(self.n_layers)
        )


def build_paper_model(spec: PaperModelSpec) -> nn.Module:
    if spec.kind in {"fno", "tfno", "hybrid_tfno", "hybrid_div"}:
        factorization = "tucker" if spec.kind in {"tfno", "hybrid_tfno", "hybrid_div"} else None
        rank = spec.tfno_rank if spec.kind in {"tfno", "hybrid_tfno", "hybrid_div"} else 1.0
        model_class = (
            HybridTFNO2d if spec.kind in {"hybrid_tfno", "hybrid_div"} else NeuralOpFNO
        )
        model: nn.Module = model_class(
            n_modes=spec.effective_modes,
            in_channels=spec.in_channels,
            out_channels=spec.out_channels,
            hidden_channels=spec.width,
            n_layers=spec.layers,
            domain_padding=spec.domain_padding,
            norm="instance_norm",
            factorization=factorization,
            rank=rank,
            implementation="factorized",
            positional_embedding="grid",
        )
    elif spec.kind == "ffno":
        model = FFNO2d(
            spec.in_channels,
            spec.out_channels,
            min(spec.effective_modes),
            spec.width,
            spec.layers,
            spec.domain_padding,
        )
    elif spec.kind == "unet":
        model = UNet2d(
            spec.in_channels,
            spec.out_channels,
            features=spec.unet_features,
            depth=spec.unet_depth,
        )
    else:
        raise ValueError(f"Unknown paper model kind: {spec.kind}")
    if not spec.alpha_bounded:
        return model
    if spec.alpha_normalized_lower is None or spec.alpha_normalized_upper is None:
        raise ValueError("Bounded alpha output requires normalized lower and upper bounds.")
    return BoundedAlphaOutput(
        model,
        spec.alpha_output_indices,
        spec.alpha_normalized_lower,
        spec.alpha_normalized_upper,
    )


def real_scalar_parameters(model: nn.Module) -> int:
    return sum(
        parameter.numel() * (2 if parameter.is_complex() else 1) for parameter in model.parameters()
    )
