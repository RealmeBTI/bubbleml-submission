# Resolution-Control Experiment: 96×96 Tutorial Split

## Purpose

Cell 2 of the paper revision: T-FNO and U-Net trained at 96×96 on the same
tutorial-split conditions used for the existing 48×48 results (Twall-103 train /
Twall-106 val / Twall-100 test).

## Design

- Resolution: 96×96 (downsampled from native 384×384, bilinear for continuous fields,
  nearest-neighbor for binary alpha/dfun mask — identical to cross-condition convention)
- Models: tfno, unet
- Seeds: 42, 100, 1234, 2025, 9999, 7, 17  (7 paired seeds)
- Split: explicit tutorial split (same trajectory assignment as n=11 48×48 run)
- Fourier modes: 24 (same cap as 48×48; well below 96/2+1=49 Nyquist ceiling)
- Training: AdamW lr=1e-3, wd=0.01, batch=8, grad-clip=1.0, 200-epoch ceiling,
  two-window validation-plateau stop, horizontal-reflection augmentation

## Contents (populated by Kaggle run)

- tfno_seed_{seed}/config.yaml  — full config + git commit + model spec
- tfno_seed_{seed}/results.json — per-epoch history + final metrics
- tfno_seed_{seed}/loss_curve.png
- unet_seed_{seed}/             — same structure

## Goal

Isolate resolution as the sole varying factor; determine whether the T-FNO/U-Net
ranking observed at 48×48 (n=11) holds, reverses, or is inconclusive at 96×96 (n=7).
