"""Train real-data FNO and U-Net checkpoints for the BubbleML comparison."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader

from .data import ChannelNormalizer, DatasetValidationError, TensorSampleDataset
from .metrics import divergence
from .models import ModelSpec, build_model
from .runtime import autocast_enabled, available_device, device_autocast, fno_device, set_seed

DEFAULT_SEEDS = (42, 100, 1234, 2025, 9999, 777, 888, 31415, 27182, 1337)


@dataclass(frozen=True)
class TrainingConfig:
    data_dir: str
    checkpoints_dir: str = "checkpoints"
    seeds: tuple[int, ...] = DEFAULT_SEEDS
    models: tuple[Literal["fno", "unet"], ...] = ("fno", "unet")
    epochs: int = 100
    batch_size: int = 2
    num_workers: int = 0
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    physics_weight: float = 0.0
    device: str = "auto"
    fno_device: str = "auto"
    use_amp: bool = False
    fno_modes: tuple[int, int] = (12, 12)
    fno_width: int = 32
    fno_layers: int = 4
    fno_padding: int = 8
    unet_features: int = 32
    unet_depth: int = 4
    allow_train_as_val: bool = False


def _loader(dataset: TensorSampleDataset, config: TrainingConfig, shuffle: bool, seed: int) -> DataLoader:
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=shuffle,
        num_workers=config.num_workers,
        pin_memory=False,  # pinning only benefits CUDA host-to-device transfers.
        persistent_workers=config.num_workers > 0,
        generator=generator,
    )


def train_epoch(
    model: torch.nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    normalizer: ChannelNormalizer,
    channel_names: tuple[str, ...],
    device: torch.device,
    model_kind: Literal["fno", "unet"],
    *,
    physics_weight: float = 0.0,
    use_amp: bool = False,
) -> dict[str, float]:
    """One epoch of normalized data loss plus optional physical divergence loss.

    Momentum/energy residuals are deliberately not imposed here: BubbleML's
    original ``pressure`` is a pressure gradient and the released fields are
    non-dimensional, so the V7 SI-constant residuals were not valid.
    """
    model.train()
    data_total = 0.0
    physics_total = 0.0
    examples = 0
    amp = autocast_enabled(device, use_amp, model_kind)
    for batch in dataloader:
        inputs = batch["input"].to(device, non_blocking=device.type == "cuda")
        targets = batch["target"].to(device, non_blocking=device.type == "cuda")
        optimizer.zero_grad(set_to_none=True)
        with device_autocast(device, amp):
            prediction = model(inputs)
            data_loss = F.mse_loss(prediction, targets)
            if physics_weight:
                physical_prediction = normalizer.decode(prediction.float())
                div = divergence(
                    physical_prediction,
                    channel_names,
                    batch["dx"].to(device, dtype=torch.float32),
                    batch["dy"].to(device, dtype=torch.float32),
                )
                physics_loss = div.square().mean()
            else:
                physics_loss = torch.zeros((), device=device)
            loss = data_loss + physics_weight * physics_loss
        loss.backward()
        optimizer.step()
        size = int(inputs.shape[0])
        examples += size
        data_total += float(data_loss.detach().item()) * size
        physics_total += float(physics_loss.detach().item()) * size
    if not examples:
        raise RuntimeError("Training DataLoader yielded no batches.")
    return {"data_mse": data_total / examples, "divergence_mse": physics_total / examples}


@torch.inference_mode()
def validation_mse(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    model_kind: Literal["fno", "unet"],
    use_amp: bool,
) -> float:
    model.eval()
    total = 0.0
    examples = 0
    amp = autocast_enabled(device, use_amp, model_kind)
    for batch in dataloader:
        inputs = batch["input"].to(device, non_blocking=device.type == "cuda")
        targets = batch["target"].to(device, non_blocking=device.type == "cuda")
        with device_autocast(device, amp):
            total += float(F.mse_loss(model(inputs), targets).item()) * int(inputs.shape[0])
        examples += int(inputs.shape[0])
    if not examples:
        raise RuntimeError("Validation DataLoader yielded no batches.")
    return total / examples


def _spec(kind: Literal["fno", "unet"], channels: int, config: TrainingConfig) -> ModelSpec:
    return ModelSpec(
        kind=kind,
        in_channels=channels,
        out_channels=channels,
        fno_modes=config.fno_modes,
        fno_width=config.fno_width,
        fno_layers=config.fno_layers,
        fno_padding=config.fno_padding,
        unet_features=config.unet_features,
        unet_depth=config.unet_depth,
    )


def _checkpoint_path(checkpoints_dir: Path, kind: str, seed: int) -> Path:
    return checkpoints_dir / f"{kind}_seed_{seed}.pt"


def train_all(config: TrainingConfig) -> list[Path]:
    if config.epochs < 1 or config.batch_size < 1:
        raise ValueError("epochs and batch_size must be positive.")
    raw_train = TensorSampleDataset(config.data_dir, split="train")
    normalizer = ChannelNormalizer.fit(raw_train)
    train_set = TensorSampleDataset(config.data_dir, split="train", normalizer=normalizer)
    try:
        validation_set = TensorSampleDataset(config.data_dir, split="val", normalizer=normalizer)
    except DatasetValidationError:
        if not config.allow_train_as_val:
            raise RuntimeError(
                "No validation split is available. Use at least two source trajectories, or explicitly "
                "pass --allow-train-as-val for a smoke test only."
            )
        print("[WARN] Using train split as validation for a smoke test; do not report these results.")
        validation_set = train_set
    checkpoints_dir = Path(config.checkpoints_dir).expanduser().resolve()
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    default_device = available_device(config.device)
    for kind in config.models:
        spec = _spec(kind, len(raw_train.channel_names), config)
        for seed in config.seeds:
            set_seed(seed)
            if kind == "fno":
                device_request = config.fno_device if config.fno_device != "auto" else config.device
                device = fno_device(device_request, spec, sample_shape=train_set[0]["input"].shape[-2:])
            else:
                device = default_device
            model = build_model(spec).to(device)
            optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
            train_loader = _loader(train_set, config, shuffle=True, seed=seed)
            val_loader = _loader(validation_set, config, shuffle=False, seed=seed)
            best_val = float("inf")
            destination = _checkpoint_path(checkpoints_dir, kind, seed)
            for epoch in range(1, config.epochs + 1):
                losses = train_epoch(
                    model,
                    train_loader,
                    optimizer,
                    normalizer,
                    raw_train.channel_names,
                    device,
                    kind,
                    physics_weight=config.physics_weight,
                    use_amp=config.use_amp,
                )
                val_loss = validation_mse(model, val_loader, device, kind, config.use_amp)
                print(
                    f"{kind.upper()} seed={seed} epoch={epoch:04d} "
                    f"train_mse={losses['data_mse']:.6e} div_mse={losses['divergence_mse']:.6e} "
                    f"val_mse={val_loss:.6e} device={device}"
                )
                if val_loss < best_val:
                    best_val = val_loss
                    torch.save(
                        {
                            "format": "bubbleml-benchmark-checkpoint-v1",
                            "model_kind": kind,
                            "seed": seed,
                            "model_spec": spec.state_dict(),
                            "model_state_dict": model.state_dict(),
                            "normalizer": normalizer.state_dict(),
                            "channel_names": list(raw_train.channel_names),
                            "best_validation_mse": best_val,
                            "training_config": asdict(config),
                        },
                        destination,
                    )
            saved.append(destination)
    return saved


def _parse_seeds(value: str) -> tuple[int, ...]:
    values = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train FNO and U-Net on real preprocessed BubbleML tensors.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--checkpoints-dir", default="checkpoints")
    parser.add_argument("--seeds", type=_parse_seeds, default=DEFAULT_SEEDS)
    parser.add_argument("--models", choices=("fno", "unet"), nargs="+", default=("fno", "unet"))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--physics-weight", type=float, default=0.0)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "mps", "cuda"))
    parser.add_argument("--fno-device", default="auto", choices=("auto", "cpu", "mps", "cuda"))
    parser.add_argument("--use-amp", action="store_true")
    parser.add_argument("--fno-modes", type=int, nargs=2, default=(12, 12))
    parser.add_argument("--fno-width", type=int, default=32)
    parser.add_argument("--fno-layers", type=int, default=4)
    parser.add_argument("--fno-padding", type=int, default=8)
    parser.add_argument("--unet-features", type=int, default=32)
    parser.add_argument("--unet-depth", type=int, default=4)
    parser.add_argument("--allow-train-as-val", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = TrainingConfig(
        data_dir=args.data_dir,
        checkpoints_dir=args.checkpoints_dir,
        seeds=args.seeds,
        models=tuple(args.models),
        epochs=args.epochs,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        physics_weight=args.physics_weight,
        device=args.device,
        fno_device=args.fno_device,
        use_amp=args.use_amp,
        fno_modes=tuple(args.fno_modes),
        fno_width=args.fno_width,
        fno_layers=args.fno_layers,
        fno_padding=args.fno_padding,
        unet_features=args.unet_features,
        unet_depth=args.unet_depth,
        allow_train_as_val=args.allow_train_as_val,
    )
    paths = train_all(config)
    print("Saved checkpoints:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
