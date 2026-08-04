"""Compute-bounded, paper-oriented training for the five-field BubbleML task."""

from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib
import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader

from .data import CHANNEL_ALPHA, CHANNEL_TEMPERATURE, ChannelNormalizer, TensorSampleDataset
from .metrics import _interface_band
from .paper_models import (
    PaperModelKind,
    PaperModelSpec,
    build_paper_model,
    real_scalar_parameters,
)
from .runtime import available_device, set_seed, synchronize
from .temporal import TemporalBundleDataset

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DEFAULT_PAPER_SEEDS = (42, 100, 1234, 2025, 9999)
DEFAULT_PAPER_MODELS: tuple[PaperModelKind, ...] = ("fno", "tfno", "ffno", "unet")
PAPER_MODEL_CHOICES: tuple[PaperModelKind, ...] = (
    "fno",
    "tfno",
    "hybrid_tfno",
    "hybrid_div",
    "ffno",
    "unet",
)


@dataclass(frozen=True)
class PaperTrainingConfig:
    data_dir: str
    experiment_dir: str = "experiments/phase1_paper"
    checkpoints_dir: str = "checkpoints/phase1_paper"
    seeds: tuple[int, ...] = DEFAULT_PAPER_SEEDS
    models: tuple[PaperModelKind, ...] = DEFAULT_PAPER_MODELS
    max_epochs: int = 200
    min_epochs: int = 20
    batch_size: int = 8
    num_workers: int = 0
    cache_frames: bool = False
    history_size: int = 5
    future_size: int = 5
    learning_rate: float = 1e-3
    weight_decay: float = 0.01
    warmup_fraction: float = 0.03
    step_factor: float = 0.5
    step_patience_epochs: int = 75
    gradient_clip: float = 1.0
    horizontal_reflection: bool = True
    fourier_downsample_factor: int = 1
    requested_modes: int = 24
    fno_width: int = 64
    fno_layers: int = 4
    ffno_width: int = 64
    ffno_layers: int = 4
    tfno_rank: float = 0.1
    unet_features: int = 32
    unet_depth: int = 4
    domain_padding: float = 0.1
    plateau_window: int = 5
    plateau_patience_windows: int = 2
    plateau_relative_delta: float = 1e-3
    max_minutes_per_run: float = 0.0
    device: str = "auto"
    bound_alpha_output: bool = False
    lambda_div: float = 0.0


def git_revision(root: Path) -> str:
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=5
    ).strip()
    if len(revision) != 40:
        raise RuntimeError(f"Expected a full git hash, got {revision!r}.")
    return revision


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def _tensor_state_dict(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    """Strip NeuralOperator's callable/class metadata from serialized weights.

    The architecture is already represented by ``PaperModelSpec``. Keeping
    only tensors makes the complete checkpoint compatible with PyTorch's
    fail-closed ``weights_only=True`` loader.
    """
    state = model.state_dict()
    unsafe = [name for name, value in state.items() if not isinstance(value, torch.Tensor)]
    unexpected = [name for name in unsafe if name != "_metadata"]
    if unexpected:
        raise TypeError(f"Model state has unexpected non-tensor entries: {unexpected}")
    return {
        name: value.detach().cpu()
        for name, value in state.items()
        if isinstance(value, torch.Tensor)
    }


def _loader(
    dataset: TemporalBundleDataset, config: PaperTrainingConfig, shuffle: bool, seed: int
) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=shuffle,
        num_workers=config.num_workers,
        persistent_workers=config.num_workers > 0,
        generator=torch.Generator().manual_seed(seed),
    )


def _resize(tensor: torch.Tensor, factor: int) -> torch.Tensor:
    if factor == 1:
        return tensor
    unbatched = tensor.ndim == 3
    if tensor.ndim not in (3, 4):
        raise ValueError(f"Expected CxHxW or BxCxHxW tensor, got {tuple(tensor.shape)}.")
    values = tensor.unsqueeze(0) if unbatched else tensor
    resized = F.interpolate(
        values,
        size=(tensor.shape[-2] // factor, tensor.shape[-1] // factor),
        mode="bilinear",
        align_corners=False,
    )
    return resized[0] if unbatched else resized


def _learning_rate(
    config: PaperTrainingConfig, step: int, total_steps: int, steps_per_epoch: int
) -> float:
    warmup = max(1, round(config.warmup_fraction * total_steps))
    if step < warmup:
        return config.learning_rate * (step + 1) / warmup
    decay_period = max(1, config.step_patience_epochs * steps_per_epoch)
    decays = (step - warmup) // decay_period
    return config.learning_rate * config.step_factor**decays


def _spec(
    kind: PaperModelKind,
    dataset: TemporalBundleDataset,
    config: PaperTrainingConfig,
    normalizer: ChannelNormalizer,
) -> PaperModelSpec:
    height, width = dataset[0]["input"].shape[-2:]
    train_height = height if kind == "unet" else height // config.fourier_downsample_factor
    train_width = width if kind == "unet" else width // config.fourier_downsample_factor
    effective = min(config.requested_modes, train_height // 2 + 1, train_width // 2 + 1)
    width_value = config.ffno_width if kind == "ffno" else config.fno_width
    layers = config.ffno_layers if kind == "ffno" else config.fno_layers
    alpha_index = dataset.channel_names.index(CHANNEL_ALPHA)
    alpha_mean = float(normalizer.mean[alpha_index])
    alpha_std = float(normalizer.std[alpha_index])
    return PaperModelSpec(
        kind=kind,
        in_channels=dataset.in_channels,
        out_channels=dataset.out_channels,
        requested_modes=(config.requested_modes, config.requested_modes),
        effective_modes=(effective, effective),
        width=width_value,
        layers=layers,
        domain_padding=config.domain_padding,
        tfno_rank=config.tfno_rank,
        unet_features=config.unet_features,
        unet_depth=config.unet_depth,
        alpha_bounded=config.bound_alpha_output,
        alpha_output_indices=tuple(
            future * normalizer.channels + alpha_index for future in range(config.future_size)
        )
        if config.bound_alpha_output
        else (),
        alpha_normalized_lower=(0.0 - alpha_mean) / alpha_std
        if config.bound_alpha_output
        else None,
        alpha_normalized_upper=(1.0 - alpha_mean) / alpha_std
        if config.bound_alpha_output
        else None,
    )


def _move_model_with_probe(
    model: torch.nn.Module,
    spec: PaperModelSpec,
    requested: str,
    sample: torch.Tensor,
) -> tuple[torch.nn.Module, torch.device]:
    device = available_device(requested)
    try:
        model = model.to(device)
        if device.type == "mps" and spec.kind != "unet":
            probe = sample.unsqueeze(0).to(device)
            model(probe).square().mean().backward()
            model.zero_grad(set_to_none=True)
            torch.mps.synchronize()
        return model, device
    except (RuntimeError, NotImplementedError) as exc:
        if device.type != "mps":
            raise
        print(f"[WARN] {spec.kind} MPS FFT probe failed ({exc}); using CPU.")
        return build_paper_model(spec).cpu(), torch.device("cpu")


def _plateau_status(
    history: list[dict[str, float]], config: PaperTrainingConfig
) -> tuple[bool, float | None]:
    window = config.plateau_window
    if len(history) < max(config.min_epochs, 2 * window):
        return False, None
    previous = sum(row["val_mse"] for row in history[-2 * window : -window]) / window
    recent = sum(row["val_mse"] for row in history[-window:]) / window
    relative_improvement = (previous - recent) / max(abs(previous), 1e-12)
    return relative_improvement < config.plateau_relative_delta, relative_improvement


@torch.inference_mode()
def _validation_mse(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> float:
    model.eval()
    total = 0.0
    elements = 0
    for batch in loader:
        inputs = batch["input"].to(device)
        targets = batch["target"].to(device)
        prediction = model(inputs)
        total += F.mse_loss(prediction, targets, reduction="sum").item()
        elements += targets.numel()
    return total / elements


def spectral_divergence_mae(
    prediction: torch.Tensor,
    normalizer: ChannelNormalizer,
    channel_names: tuple[str, ...],
    future_size: int,
    dx: torch.Tensor,
    dy: torch.Tensor,
) -> torch.Tensor:
    """Mean absolute physical velocity divergence from Fourier derivatives."""
    if prediction.ndim != 4:
        raise ValueError(f"Expected Bx(T*C)xHxW prediction, got {tuple(prediction.shape)}.")
    batch, flattened_channels, height, width = prediction.shape
    channels = len(channel_names)
    if flattened_channels != future_size * channels:
        raise ValueError("Prediction channels do not match future_size * field channels.")
    if dx.numel() != batch or dy.numel() != batch:
        raise ValueError("dx and dy must contain one spacing per batch element.")

    shaped = prediction.float().view(batch, future_size, channels, height, width)
    mean = normalizer.mean.to(shaped).view(1, 1, channels, 1, 1)
    std = normalizer.std.to(shaped).view(1, 1, channels, 1, 1)
    physical = shaped * std + mean
    u = physical[:, :, channel_names.index("u")]
    v = physical[:, :, channel_names.index("v")]

    kx = 2 * torch.pi * torch.fft.fftfreq(width, device=prediction.device)
    ky = 2 * torch.pi * torch.fft.fftfreq(height, device=prediction.device)
    kx = kx.view(1, 1, 1, width) / dx.to(prediction).view(batch, 1, 1, 1)
    ky = ky.view(1, 1, height, 1) / dy.to(prediction).view(batch, 1, 1, 1)
    divergence_hat = 1j * kx * torch.fft.fft2(u) + 1j * ky * torch.fft.fft2(v)
    divergence = torch.fft.ifft2(divergence_hat).real
    return divergence.abs().mean()


@torch.inference_mode()
def _validation_losses(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
    normalizer: ChannelNormalizer,
    channel_names: tuple[str, ...],
    future_size: int,
) -> tuple[float, float, float]:
    model.eval()
    squared_error = 0.0
    elements = 0
    divergence_total = 0.0
    examples = 0
    interface_total = 0.0
    interface_values = 0
    for batch in loader:
        inputs = batch["input"].to(device)
        targets = batch["target"].to(device)
        prediction = model(inputs)
        squared_error += F.mse_loss(prediction, targets, reduction="sum").item()
        elements += targets.numel()
        size = int(inputs.shape[0])
        divergence_total += float(
            spectral_divergence_mae(
                prediction,
                normalizer,
                channel_names,
                future_size,
                batch["dx"].to(device, dtype=torch.float32),
                batch["dy"].to(device, dtype=torch.float32),
            ).item()
        ) * size
        shaped_prediction = prediction.float().view(
            size, future_size, len(channel_names), *prediction.shape[-2:]
        )
        shaped_target = targets.float().view(
            size, future_size, len(channel_names), *targets.shape[-2:]
        )
        mean = normalizer.mean.to(shaped_prediction).view(1, 1, -1, 1, 1)
        std = normalizer.std.to(shaped_prediction).view(1, 1, -1, 1, 1)
        physical_prediction = shaped_prediction * std + mean
        physical_target = shaped_target * std + mean
        alpha_index = channel_names.index(CHANNEL_ALPHA)
        temperature_index = channel_names.index(CHANNEL_TEMPERATURE)
        alpha_target = physical_target[:, :, alpha_index].flatten(0, 1).unsqueeze(1)
        interface = _interface_band(alpha_target)[:, 0]
        temperature_error = (
            physical_prediction[:, :, temperature_index]
            - physical_target[:, :, temperature_index]
        ).flatten(0, 1)
        interface_counts = interface.sum(dim=(-2, -1))
        valid = interface_counts > 0
        if valid.any():
            frame_rmse = torch.sqrt(
                (temperature_error.square() * interface).sum(dim=(-2, -1))[valid]
                / interface_counts[valid]
            )
            interface_total += float(frame_rmse.sum().item())
            interface_values += int(valid.sum().item())
        examples += size
    if interface_values == 0:
        raise RuntimeError("Validation split contains no defined interface-temperature values.")
    interface_rmse = interface_total / interface_values
    return squared_error / elements, divergence_total / examples, interface_rmse


def _plot_history(history: list[dict[str, float]], destination: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    epochs = [row["epoch"] for row in history]
    ax.semilogy(epochs, [row["train_mse"] for row in history], label="train")
    ax.semilogy(epochs, [row["val_mse"] for row in history], label="validation")
    ax.set(xlabel="Epoch", ylabel="Normalized MSE")
    ax.legend()
    fig.tight_layout()
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def train_all(config: PaperTrainingConfig, workspace: Path | None = None) -> list[Path]:
    workspace = (workspace or Path.cwd()).resolve()
    if config.lambda_div < 0:
        raise ValueError("lambda_div must be non-negative.")
    if "hybrid_div" in config.models and config.lambda_div <= 0:
        raise ValueError("hybrid_div requires a positive lambda_div.")
    if config.lambda_div and any(kind != "hybrid_div" for kind in config.models):
        raise ValueError("lambda_div is restricted to hybrid_div training runs.")
    revision = git_revision(workspace)
    raw_train = TensorSampleDataset(config.data_dir, split="train")
    normalizer = ChannelNormalizer.fit(raw_train)
    train_set = TemporalBundleDataset(
        config.data_dir,
        "train",
        normalizer,
        history_size=config.history_size,
        future_size=config.future_size,
        cache_frames=config.cache_frames,
    )
    val_set = TemporalBundleDataset(
        config.data_dir,
        "val",
        normalizer,
        history_size=config.history_size,
        future_size=config.future_size,
        cache_frames=config.cache_frames,
    )
    checkpoints = Path(config.checkpoints_dir).resolve()
    experiments = Path(config.experiment_dir).resolve()
    saved: list[Path] = []

    for kind in config.models:
        spec = _spec(kind, train_set, config, normalizer)
        for seed in config.seeds:
            set_seed(seed)
            run_dir = experiments / f"{kind}_seed_{seed}"
            run_dir.mkdir(parents=True, exist_ok=True)
            run_config = {
                **asdict(config),
                "model": kind,
                "seed": seed,
                "git_commit": revision,
                "model_spec": spec.state_dict(),
                "protocol": "custom-five-field-temporal-bundle",
                "resolution_policy": {
                    "native": [
                        int(train_set[0]["input"].shape[-2]),
                        int(train_set[0]["input"].shape[-1]),
                    ],
                    "training": [
                        int(
                            train_set[0]["input"].shape[-2]
                            // (1 if kind == "unet" else config.fourier_downsample_factor)
                        ),
                        int(
                            train_set[0]["input"].shape[-1]
                            // (1 if kind == "unet" else config.fourier_downsample_factor)
                        ),
                    ],
                    "requested_modes": list(spec.requested_modes) if kind != "unet" else None,
                    "effective_modes": list(spec.effective_modes) if kind != "unet" else None,
                    "nyquist_note": "For N=48, a real FFT has N/2+1=25 unique bins; use 24 modes just below that ceiling.",
                },
            }
            _atomic_json(run_dir / "config.yaml", run_config)

            model = build_paper_model(spec)
            train_factor = 1 if kind == "unet" else config.fourier_downsample_factor
            probe = _resize(train_set[0]["input"], train_factor)
            model, device = _move_model_with_probe(model, spec, config.device, probe)
            optimizer = torch.optim.AdamW(
                model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
            )
            train_loader = _loader(train_set, config, True, seed)
            val_loader = _loader(val_set, config, False, seed)
            total_steps = config.max_epochs * len(train_loader)
            global_step = 0
            history: list[dict[str, float]] = []
            best_val = float("inf")
            best_val_divergence = float("inf")
            best_val_interface_temperature_rmse = float("inf")
            best_epoch = 0
            plateau_windows = 0
            stopped_reason = "max_epochs"
            started = time.perf_counter()
            destination = checkpoints / f"{kind}_seed_{seed}.pt"
            destination.parent.mkdir(parents=True, exist_ok=True)

            for epoch in range(1, config.max_epochs + 1):
                epoch_started = time.perf_counter()
                model.train()
                squared_error = 0.0
                elements = 0
                gradient_norm_total = 0.0
                divergence_total = 0.0
                training_examples = 0
                batches = 0
                for batch in train_loader:
                    inputs = batch["input"]
                    targets = batch["target"]
                    if config.horizontal_reflection and torch.rand(()) < 0.5:
                        inputs = torch.flip(inputs, dims=(-1,))
                        targets = torch.flip(targets, dims=(-1,))
                    inputs = _resize(inputs, train_factor).to(device)
                    targets = _resize(targets, train_factor).to(device)
                    lr = _learning_rate(config, global_step, total_steps, len(train_loader))
                    for group in optimizer.param_groups:
                        group["lr"] = lr
                    optimizer.zero_grad(set_to_none=True)
                    prediction = model(inputs)
                    data_loss = F.mse_loss(prediction, targets)
                    if config.lambda_div:
                        divergence_loss = spectral_divergence_mae(
                            prediction,
                            normalizer,
                            train_set.channel_names,
                            config.future_size,
                            batch["dx"].to(device, dtype=torch.float32),
                            batch["dy"].to(device, dtype=torch.float32),
                        )
                    else:
                        divergence_loss = torch.zeros((), device=device)
                    loss = data_loss + config.lambda_div * divergence_loss
                    loss.backward()
                    gradient_norm = torch.nn.utils.clip_grad_norm_(
                        model.parameters(), config.gradient_clip
                    )
                    optimizer.step()
                    squared_error += F.mse_loss(
                        prediction.detach(), targets, reduction="sum"
                    ).item()
                    elements += targets.numel()
                    gradient_norm_total += float(gradient_norm)
                    divergence_total += float(divergence_loss.detach()) * int(inputs.shape[0])
                    training_examples += int(inputs.shape[0])
                    batches += 1
                    global_step += 1

                val_mse, val_divergence, val_interface_temperature_rmse = _validation_losses(
                    model,
                    val_loader,
                    device,
                    normalizer,
                    val_set.channel_names,
                    config.future_size,
                )
                synchronize(device)
                row = {
                    "epoch": float(epoch),
                    "train_mse": squared_error / elements,
                    "val_mse": val_mse,
                    "learning_rate": optimizer.param_groups[0]["lr"],
                    "gradient_norm_before_clip": gradient_norm_total / batches,
                    "train_divergence_mae": divergence_total / training_examples,
                    "val_divergence_mae": val_divergence,
                    "val_interface_temperature_rmse": val_interface_temperature_rmse,
                    "train_total_loss": squared_error / elements
                    + config.lambda_div * divergence_total / training_examples,
                    "epoch_seconds": time.perf_counter() - epoch_started,
                }
                history.append(row)
                plateau_candidate, relative_improvement = _plateau_status(history, config)
                row["plateau_relative_improvement"] = (
                    float(relative_improvement) if relative_improvement is not None else math.nan
                )
                plateau_windows = plateau_windows + 1 if plateau_candidate else 0
                plateau_reached = plateau_windows >= config.plateau_patience_windows
                print(
                    f"{kind.upper()} seed={seed} epoch={epoch:04d} "
                    f"train={row['train_mse']:.6e} val={val_mse:.6e} "
                    f"div={row['train_divergence_mae']:.6e} val_div={val_divergence:.6e} "
                    f"val_interface_t={val_interface_temperature_rmse:.6e} "
                    f"lr={row['learning_rate']:.3e} seconds={row['epoch_seconds']:.2f}",
                    flush=True,
                )
                if val_mse < best_val:
                    best_val = val_mse
                    best_val_divergence = val_divergence
                    best_val_interface_temperature_rmse = val_interface_temperature_rmse
                    best_epoch = epoch
                    checkpoint = {
                        "format": "bubbleml-paper-five-field-v1",
                        "model_kind": kind,
                        "seed": seed,
                        "git_commit": revision,
                        "model_spec": spec.state_dict(),
                        "model_state_dict": _tensor_state_dict(model),
                        "normalizer": normalizer.state_dict(),
                        "channel_names": list(raw_train.channel_names),
                        "history_size": config.history_size,
                        "future_size": config.future_size,
                        "best_validation_mse": best_val,
                        "best_validation_divergence_mae": best_val_divergence,
                        "best_validation_interface_temperature_rmse": best_val_interface_temperature_rmse,
                        "best_epoch": best_epoch,
                        "training_config": asdict(config),
                        "history": history,
                    }
                    torch.save(checkpoint, destination)
                progress = {
                    "status": "running",
                    "model": kind,
                    "seed": seed,
                    "git_commit": revision,
                    "history": history,
                    "best_validation_mse": best_val,
                    "best_validation_divergence_mae": best_val_divergence,
                    "best_validation_interface_temperature_rmse": best_val_interface_temperature_rmse,
                    "best_epoch": best_epoch,
                    "plateau_reached": plateau_reached,
                }
                _atomic_json(run_dir / "results.json", progress)
                if plateau_reached:
                    stopped_reason = "validation_plateau"
                    break
                elapsed_minutes = (time.perf_counter() - started) / 60
                if config.max_minutes_per_run and elapsed_minutes >= config.max_minutes_per_run:
                    stopped_reason = "time_limit_before_plateau"
                    break

            checkpoint = torch.load(destination, map_location="cpu", weights_only=True)
            checkpoint["history"] = history
            torch.save(checkpoint, destination)
            saved.append(destination)
            final = {
                "status": "completed",
                "model": kind,
                "seed": seed,
                "git_commit": revision,
                "history": history,
                "best_validation_mse": best_val,
                "best_validation_divergence_mae": best_val_divergence,
                "best_validation_interface_temperature_rmse": best_val_interface_temperature_rmse,
                "best_epoch": best_epoch,
                "stopped_reason": stopped_reason,
                "plateau_reached": stopped_reason == "validation_plateau",
                "wall_seconds": time.perf_counter() - started,
                "parameters": sum(parameter.numel() for parameter in model.parameters()),
                "real_scalar_parameters": real_scalar_parameters(model),
                "device": str(device),
                "requested_modes": list(spec.requested_modes),
                "effective_modes": list(spec.effective_modes),
                "checkpoint": str(destination),
                "runtime": {
                    "python": platform.python_version(),
                    "torch": torch.__version__,
                    "mps_available": torch.backends.mps.is_available(),
                    "cuda_available": torch.cuda.is_available(),
                },
            }
            _atomic_json(run_dir / "results.json", final)
            _plot_history(history, run_dir / "loss_curve.png")
    return saved


def _csv_ints(value: str) -> tuple[int, ...]:
    result = tuple(int(item) for item in value.split(",") if item.strip())
    if not result:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--experiment-dir", default="experiments/phase1_paper")
    parser.add_argument("--checkpoints-dir", default="checkpoints/phase1_paper")
    parser.add_argument("--seeds", type=_csv_ints, default=DEFAULT_PAPER_SEEDS)
    parser.add_argument(
        "--models", nargs="+", choices=PAPER_MODEL_CHOICES, default=DEFAULT_PAPER_MODELS
    )
    parser.add_argument("--max-epochs", type=int, default=200)
    parser.add_argument("--min-epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--cache-frames", action="store_true")
    parser.add_argument("--history-size", type=int, default=5)
    parser.add_argument("--future-size", type=int, default=5)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-fraction", type=float, default=0.03)
    parser.add_argument("--step-factor", type=float, default=0.5)
    parser.add_argument("--step-patience-epochs", type=int, default=75)
    parser.add_argument("--gradient-clip", type=float, default=1.0)
    parser.add_argument("--fourier-downsample-factor", type=int, default=1)
    parser.add_argument("--requested-modes", type=int, default=24)
    parser.add_argument("--fno-width", type=int, default=64)
    parser.add_argument("--fno-layers", type=int, default=4)
    parser.add_argument("--ffno-width", type=int, default=64)
    parser.add_argument("--ffno-layers", type=int, default=4)
    parser.add_argument("--tfno-rank", type=float, default=0.1)
    parser.add_argument("--unet-features", type=int, default=32)
    parser.add_argument("--unet-depth", type=int, default=4)
    parser.add_argument("--domain-padding", type=float, default=0.1)
    parser.add_argument("--plateau-window", type=int, default=5)
    parser.add_argument("--plateau-patience-windows", type=int, default=2)
    parser.add_argument("--plateau-relative-delta", type=float, default=1e-3)
    parser.add_argument("--max-minutes-per-run", type=float, default=0.0)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    parser.add_argument("--no-horizontal-reflection", action="store_true")
    parser.add_argument("--bound-alpha-output", action="store_true")
    parser.add_argument("--lambda-div", type=float, default=0.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = PaperTrainingConfig(
        data_dir=args.data_dir,
        experiment_dir=args.experiment_dir,
        checkpoints_dir=args.checkpoints_dir,
        seeds=args.seeds,
        models=tuple(args.models),
        max_epochs=args.max_epochs,
        min_epochs=args.min_epochs,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        cache_frames=args.cache_frames,
        history_size=args.history_size,
        future_size=args.future_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_fraction=args.warmup_fraction,
        step_factor=args.step_factor,
        step_patience_epochs=args.step_patience_epochs,
        gradient_clip=args.gradient_clip,
        horizontal_reflection=not args.no_horizontal_reflection,
        fourier_downsample_factor=args.fourier_downsample_factor,
        requested_modes=args.requested_modes,
        fno_width=args.fno_width,
        fno_layers=args.fno_layers,
        ffno_width=args.ffno_width,
        ffno_layers=args.ffno_layers,
        tfno_rank=args.tfno_rank,
        unet_features=args.unet_features,
        unet_depth=args.unet_depth,
        domain_padding=args.domain_padding,
        plateau_window=args.plateau_window,
        plateau_patience_windows=args.plateau_patience_windows,
        plateau_relative_delta=args.plateau_relative_delta,
        max_minutes_per_run=args.max_minutes_per_run,
        device=args.device,
        bound_alpha_output=args.bound_alpha_output,
        lambda_div=args.lambda_div,
    )
    for checkpoint in train_all(config):
        print(checkpoint)


if __name__ == "__main__":
    main()
