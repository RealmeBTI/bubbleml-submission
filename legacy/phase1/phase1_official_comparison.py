#!/usr/bin/env python3
"""Reproducible Phase-1 comparison on BubbleML's official worked example.

This runner intentionally mirrors ``examples/pytorch_training.ipynb``: two
training trajectories, one validation trajectory, one-step temperature
prediction from temperature and velocity, AdamW at 1e-4, and no normalization.
It adds deterministic seeds, epoch logs, checkpoints, metrics, and figures; it
does not replace or modify the upstream notebook run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import h5py
import matplotlib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from neuralop.models import FNO
from torch.utils.data import ConcatDataset, DataLoader, Dataset

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


class HDF5Dataset(Dataset):
    """The dataset definition used by the official BubbleML notebook."""

    def __init__(self, filename: Path):
        self.filename = filename
        self.data = h5py.File(filename, "r")
        self.timesteps = self.data["temperature"].shape[0]

    def __len__(self) -> int:
        return self.timesteps - 1

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.stack(
            (
                torch.from_numpy(self.data["temperature"][idx]),
                torch.from_numpy(self.data["velx"][idx]),
                torch.from_numpy(self.data["vely"][idx]),
            ),
            dim=0,
        )
        y = torch.from_numpy(self.data["temperature"][idx + 1]).unsqueeze(0)
        return x, y


class DoubleConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.GELU(),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MatchedUNet(nn.Module):
    """Three-level U-Net matched to FNO by conventional ``numel`` count."""

    def __init__(self, base: int = 36):
        super().__init__()
        self.enc1 = DoubleConv(3, base)
        self.enc2 = DoubleConv(base, base * 2)
        self.enc3 = DoubleConv(base * 2, base * 4)
        self.bottleneck = DoubleConv(base * 4, base * 8)
        self.pool = nn.MaxPool2d(2)
        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.dec3 = DoubleConv(base * 8, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = DoubleConv(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = DoubleConv(base * 2, base)
        self.head = nn.Conv2d(base, 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        z = self.bottleneck(self.pool(e3))
        d3 = self.dec3(torch.cat((self.up3(z), e3), dim=1))
        d2 = self.dec2(torch.cat((self.up2(d3), e2), dim=1))
        return self.head(self.dec1(torch.cat((self.up1(d2), e1), dim=1)))


@dataclass(frozen=True)
class Config:
    model: str
    seed: int
    epochs: int
    batch_size: int
    learning_rate: float
    device: str
    train_files: tuple[str, ...]
    val_files: tuple[str, ...]
    fno_modes: int = 16
    fno_hidden_channels: int = 64
    fno_layers: int = 4
    unet_base_channels: int = 36


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def real_degrees_of_freedom(model: nn.Module) -> int:
    return sum(p.numel() * (2 if p.is_complex() else 1) for p in model.parameters())


def build_model(config: Config) -> nn.Module:
    if config.model == "fno":
        return FNO(
            in_channels=3,
            out_channels=1,
            n_modes=(config.fno_modes, config.fno_modes),
            hidden_channels=config.fno_hidden_channels,
            n_layers=config.fno_layers,
        )
    return MatchedUNet(config.unet_base_channels)


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict[str, float]:
    model.eval()
    squared_error = 0.0
    boundary_squared_error = 0.0
    count = 0
    boundary_count = 0
    for x, y in loader:
        x, y = x.to(device).float(), y.to(device).float()
        pred = model(x)
        err2 = (pred - y).square()
        squared_error += err2.sum().item()
        count += err2.numel()
        mask = torch.zeros_like(err2, dtype=torch.bool)
        mask[..., 0, :] = True
        mask[..., -1, :] = True
        mask[..., :, 0] = True
        mask[..., :, -1] = True
        boundary_squared_error += err2[mask].sum().item()
        boundary_count += mask.sum().item()
    mse = squared_error / count
    boundary_mse = boundary_squared_error / boundary_count
    return {
        "mse": mse,
        "rmse": math.sqrt(mse),
        "boundary_rmse_outermost_grid": math.sqrt(boundary_mse),
    }


def git_revision(workspace: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except subprocess.TimeoutExpired:
        return "UNAVAILABLE_ICLOUD_OFFLOADED"
    except (OSError, subprocess.CalledProcessError):
        return "UNCOMMITTED_NO_HEAD"


def save_figures(
    history: list[dict[str, float]], model: nn.Module, dataset: Dataset, device: torch.device, out: Path
) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.semilogy([row["epoch"] for row in history], [row["train_mse"] for row in history], label="train")
    ax.semilogy([row["epoch"] for row in history], [row["val_mse"] for row in history], label="validation")
    ax.set(xlabel="Epoch", ylabel="MSE", title="Official BubbleML example task")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "loss_curve.png", dpi=180)
    plt.close(fig)

    indices = (35, 90, 150)
    fig, axes = plt.subplots(len(indices), 3, figsize=(9, 8), constrained_layout=True)
    model.eval()
    for row, index in enumerate(indices):
        x, y = dataset[index]
        with torch.no_grad():
            pred = model(x.unsqueeze(0).to(device).float()).squeeze().cpu().numpy()
        truth = y.squeeze().numpy()
        images = (truth, pred, np.abs(truth - pred))
        for col, image in enumerate(images):
            im = axes[row, col].imshow(np.flipud(image))
            fig.colorbar(im, ax=axes[row, col], shrink=0.65)
            axes[row, col].set_xticks([])
            axes[row, col].set_yticks([])
    for col, title in enumerate(("Ground truth", "Prediction", "Absolute error")):
        axes[0, col].set_title(title)
    fig.savefig(out / "validation_examples.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--model", choices=("fno", "unet"), required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    args = parser.parse_args()

    seed_all(args.seed)
    device = torch.device("cpu")
    train_paths = (args.data_dir / "Twall-100.hdf5", args.data_dir / "Twall-106.hdf5")
    val_paths = (args.data_dir / "Twall-103.hdf5",)
    config = Config(
        model=args.model,
        seed=args.seed,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        device=str(device),
        train_files=tuple(str(path) for path in train_paths),
        val_files=tuple(str(path) for path in val_paths),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "config.yaml").write_text(json.dumps(asdict(config), indent=2) + "\n")

    train_dataset = ConcatDataset(HDF5Dataset(path) for path in train_paths)
    val_dataset = ConcatDataset(HDF5Dataset(path) for path in val_paths)
    generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0, generator=generator
    )
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    model = build_model(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    history: list[dict[str, float]] = []
    best_mse = float("inf")
    started = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        epoch_started = time.perf_counter()
        model.train()
        train_squared_error = 0.0
        train_count = 0
        for x, y in train_loader:
            x, y = x.to(device).float(), y.to(device).float()
            pred = model(x)
            loss = F.mse_loss(pred, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_squared_error += F.mse_loss(pred.detach(), y, reduction="sum").item()
            train_count += y.numel()
        metrics = evaluate(model, val_loader, device)
        row = {
            "epoch": epoch,
            "train_mse": train_squared_error / train_count,
            "val_mse": metrics["mse"],
            "epoch_seconds": time.perf_counter() - epoch_started,
        }
        history.append(row)
        print(json.dumps(row), flush=True)
        if metrics["mse"] < best_mse:
            best_mse = metrics["mse"]
            torch.save({"model": model.state_dict(), "config": asdict(config), "epoch": epoch}, args.output / "best.pt")

    checkpoint = torch.load(args.output / "best.pt", map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model"])
    final_metrics = evaluate(model, val_loader, device)
    results: dict[str, Any] = {
        "status": "completed",
        "best_epoch": checkpoint["epoch"],
        "metrics": final_metrics,
        "history": history,
        "wall_seconds": time.perf_counter() - started,
        "trainable_tensor_elements": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "real_scalar_degrees_of_freedom": real_degrees_of_freedom(model),
        "git_revision": git_revision(args.workspace),
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "platform": platform.platform(),
            "mps_available": torch.backends.mps.is_available(),
            "cuda_available": torch.cuda.is_available(),
        },
        "data_sha256": {path.name: sha256(path) for path in (*train_paths, *val_paths)},
    }
    (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    save_figures(history, model, val_dataset, device, args.output)


if __name__ == "__main__":
    main()
