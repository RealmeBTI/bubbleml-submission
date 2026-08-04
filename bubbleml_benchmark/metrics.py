"""Error metrics that distinguish interior-edge and liquid-vapor-interface errors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

import torch
from torch.nn import functional as F

from .data import CHANNEL_ALPHA, CHANNEL_TEMPERATURE, channel_index


def fourth_order_derivative(field: torch.Tensor, spacing: float | torch.Tensor, dim: int) -> torch.Tensor:
    """Differentiate BxCxHxW fields with fourth-order interiors and one-sided edges."""
    if field.ndim != 4:
        raise ValueError(f"Expected BxCxHxW field, got {tuple(field.shape)}.")
    axis = dim if dim >= 0 else field.ndim + dim
    if axis not in (2, 3):
        raise ValueError("Only the H and W dimensions can be differentiated.")
    size = field.shape[axis]
    if size < 3:
        raise ValueError("At least three cells are required for a spatial derivative.")
    scale = torch.as_tensor(spacing, dtype=field.dtype, device=field.device)
    if scale.ndim == 0:
        scale = scale.view(1, 1, 1, 1)
    elif scale.ndim == 1 and scale.numel() == field.shape[0]:
        scale = scale.view(-1, 1, 1, 1)
    else:
        raise ValueError("spacing must be scalar or a B-element tensor.")
    output = torch.empty_like(field)
    if axis == 3:
        output[..., 0] = (-3 * field[..., 0] + 4 * field[..., 1] - field[..., 2]) / (2 * scale[..., 0])
        output[..., 1] = (field[..., 2] - field[..., 0]) / (2 * scale[..., 0])
        output[..., -2] = (field[..., -1] - field[..., -3]) / (2 * scale[..., 0])
        output[..., -1] = (3 * field[..., -1] - 4 * field[..., -2] + field[..., -3]) / (2 * scale[..., 0])
        if size > 4:
            output[..., 2:-2] = (
                -field[..., 4:] + 8 * field[..., 3:-1] - 8 * field[..., 1:-3] + field[..., :-4]
            ) / (12 * scale)
    else:
        output[..., 0, :] = (-3 * field[..., 0, :] + 4 * field[..., 1, :] - field[..., 2, :]) / (
            2 * scale[..., 0, :]
        )
        output[..., 1, :] = (field[..., 2, :] - field[..., 0, :]) / (2 * scale[..., 0, :])
        output[..., -2, :] = (field[..., -1, :] - field[..., -3, :]) / (2 * scale[..., 0, :])
        output[..., -1, :] = (3 * field[..., -1, :] - 4 * field[..., -2, :] + field[..., -3, :]) / (
            2 * scale[..., 0, :]
        )
        if size > 4:
            output[..., 2:-2, :] = (
                -field[..., 4:, :] + 8 * field[..., 3:-1, :] - 8 * field[..., 1:-3, :] + field[..., :-4, :]
            ) / (12 * scale)
    return output


def divergence(physical_state: torch.Tensor, channel_names: Sequence[str], dx: float, dy: float) -> torch.Tensor:
    u = physical_state[:, channel_index(channel_names, "u") : channel_index(channel_names, "u") + 1]
    v = physical_state[:, channel_index(channel_names, "v") : channel_index(channel_names, "v") + 1]
    return fourth_order_derivative(u, dx, -1) + fourth_order_derivative(v, dy, -2)


def _gradient_magnitude(field: torch.Tensor) -> torch.Tensor:
    """Grid-cell gradient used for weighting; avoids pretending missing x/y are physical."""
    dx = torch.zeros_like(field)
    dy = torch.zeros_like(field)
    dx[..., :, 1:] = field[..., :, 1:] - field[..., :, :-1]
    dy[..., 1:, :] = field[..., 1:, :] - field[..., :-1, :]
    return torch.sqrt(dx.square() + dy.square())


def gradient_weighted_rmse(prediction: torch.Tensor, target: torch.Tensor, weight_strength: float = 1.0) -> torch.Tensor:
    """RMSE weighted toward gradients in the reference field, separately per sample."""
    gradient = _gradient_magnitude(target)
    normalizer = gradient.mean(dim=(-2, -1), keepdim=True).clamp_min(1e-6)
    weights = 1.0 + weight_strength * gradient / normalizer
    return torch.sqrt((weights * (prediction - target).square()).sum(dim=(-3, -2, -1)) / weights.sum(dim=(-3, -2, -1)))


def _interface_band(alpha: torch.Tensor) -> torch.Tensor:
    """One-cell dilation around target vapor/liquid sign changes."""
    phase = alpha > 0.5
    edges = torch.zeros_like(phase, dtype=torch.bool)
    edges[..., 1:, :] |= phase[..., 1:, :] != phase[..., :-1, :]
    edges[..., :-1, :] |= phase[..., 1:, :] != phase[..., :-1, :]
    edges[..., :, 1:] |= phase[..., :, 1:] != phase[..., :, :-1]
    edges[..., :, :-1] |= phase[..., :, 1:] != phase[..., :, :-1]
    return F.max_pool2d(edges.float(), kernel_size=3, stride=1, padding=1).bool()


def _masked_rmse(error: torch.Tensor, mask: torch.Tensor) -> float | None:
    values = error[..., mask]
    if values.numel() == 0:
        return None
    return float(torch.sqrt(values.square().mean()).item())


def _interface_temperature_jump_error(prediction: torch.Tensor, target: torch.Tensor, alpha: torch.Tensor) -> float | None:
    """Error in local temperature jumps across true liquid-vapor crossing edges."""
    phase = alpha > 0.5
    values: list[torch.Tensor] = []
    horizontal = phase[:, 1:] != phase[:, :-1]
    if horizontal.any():
        pred_jump = prediction[:, 1:] - prediction[:, :-1]
        target_jump = target[:, 1:] - target[:, :-1]
        values.append((pred_jump - target_jump).abs()[horizontal])
    vertical = phase[1:, :] != phase[:-1, :]
    if vertical.any():
        pred_jump = prediction[1:, :] - prediction[:-1, :]
        target_jump = target[1:, :] - target[:-1, :]
        values.append((pred_jump - target_jump).abs()[vertical])
    if not values:
        return None
    return float(torch.cat(values).mean().item())


def _edge_mask(height: int, width: int, edge_width: int, device: torch.device) -> torch.Tensor:
    mask = torch.zeros(height, width, dtype=torch.bool, device=device)
    edge_width = min(edge_width, height // 2, width // 2)
    if edge_width < 1:
        return torch.ones_like(mask)
    mask[:edge_width] = True
    mask[-edge_width:] = True
    mask[:, :edge_width] = True
    mask[:, -edge_width:] = True
    return mask


def sample_metrics(
    prediction: torch.Tensor,
    target: torch.Tensor,
    channel_names: Sequence[str],
    dx: float,
    dy: float,
    edge_width: int = 2,
) -> dict[str, float | None]:
    """Metrics for one physical CxHxW prediction/target pair.

    ``boundary_*`` metrics operate on the outer interior cells present in the
    files.  They are intentionally not called physical wall residuals because
    BubbleML excludes physical boundary cells.
    """
    if prediction.shape != target.shape or prediction.ndim != 3:
        raise ValueError("prediction and target must have matching CxHxW shapes.")
    error = prediction - target
    target_norm = target.norm().clamp_min(1e-8)
    temp_idx = channel_index(channel_names, CHANNEL_TEMPERATURE)
    alpha_idx = channel_index(channel_names, CHANNEL_ALPHA)
    alpha_target = target[alpha_idx]
    interface = _interface_band(alpha_target.unsqueeze(0).unsqueeze(0))[0, 0]
    edge = _edge_mask(target.shape[-2], target.shape[-1], edge_width, target.device)
    pred_batch = prediction.unsqueeze(0)
    target_batch = target.unsqueeze(0)
    div = divergence(pred_batch, channel_names, dx, dy)[0, 0]
    metrics: dict[str, float | None] = {
        "relative_l2": float(error.norm().div(target_norm).item()),
        "rmse": float(torch.sqrt(error.square().mean()).item()),
        "gwrmse": float(gradient_weighted_rmse(pred_batch, target_batch)[0].item()),
        "temperature_gwrmse": float(
            gradient_weighted_rmse(pred_batch[:, temp_idx : temp_idx + 1], target_batch[:, temp_idx : temp_idx + 1])[0].item()
        ),
        "alpha_gwrmse": float(
            gradient_weighted_rmse(pred_batch[:, alpha_idx : alpha_idx + 1], target_batch[:, alpha_idx : alpha_idx + 1])[0].item()
        ),
        "interior_edge_rmse": _masked_rmse(error, edge),
        "interior_edge_divergence_mae": float(div[edge].abs().mean().item()),
        "mass_conservation_mae": float(div.abs().mean().item()),
        "interface_alpha_rmse": _masked_rmse(error[alpha_idx : alpha_idx + 1], interface),
        "interface_temperature_rmse": _masked_rmse(error[temp_idx : temp_idx + 1], interface),
        "interface_temperature_jump_mae": _interface_temperature_jump_error(
            prediction[temp_idx], target[temp_idx], alpha_target
        ),
    }
    return metrics


class MetricAccumulator:
    """Mean only over samples for which a metric is defined (e.g. interfaces)."""

    def __init__(self) -> None:
        self.totals: dict[str, float] = defaultdict(float)
        self.counts: dict[str, int] = defaultdict(int)

    def update(self, values: dict[str, float | None]) -> None:
        for name, value in values.items():
            if value is not None and math_isfinite(value):
                self.totals[name] += value
                self.counts[name] += 1

    def mean(self) -> dict[str, float]:
        return {name: self.totals[name] / self.counts[name] for name in sorted(self.totals) if self.counts[name]}


def math_isfinite(value: float) -> bool:
    return bool(torch.isfinite(torch.tensor(value)).item())
