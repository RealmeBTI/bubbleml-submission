#!/usr/bin/env bash
set -euo pipefail

run_candidate() {
  local label="$1"
  local lambda="$2"
  local seeds="$3"
  .venv/bin/python -m bubbleml_benchmark.paper_train \
    --data-dir data/bubbleml/smoke_restore \
    --experiment-dir "experiments/lambda_sensitivity_${label}" \
    --checkpoints-dir "checkpoints/lambda_sensitivity_${label}" \
    --seeds "$seeds" \
    --models hybrid_div \
    --max-epochs 200 \
    --min-epochs 20 \
    --batch-size 8 \
    --cache-frames \
    --history-size 5 \
    --future-size 5 \
    --learning-rate 0.001 \
    --weight-decay 0.01 \
    --warmup-fraction 0.03 \
    --step-factor 0.5 \
    --step-patience-epochs 75 \
    --gradient-clip 1.0 \
    --requested-modes 24 \
    --fno-width 64 \
    --fno-layers 4 \
    --tfno-rank 0.1 \
    --domain-padding 0.1 \
    --plateau-window 5 \
    --plateau-patience-windows 2 \
    --plateau-relative-delta 0.001 \
    --lambda-div "$lambda" \
    --device mps
}

mkdir -p checkpoints/lambda_sensitivity_001 checkpoints/lambda_sensitivity_003
cp checkpoints/tier1_div_pilot_001/hybrid_div_seed_42.pt \
  checkpoints/tier1_div_pilot_001/hybrid_div_seed_100.pt \
  checkpoints/lambda_sensitivity_001/
cp checkpoints/tier1_div_pilot_003/hybrid_div_seed_42.pt \
  checkpoints/tier1_div_pilot_003/hybrid_div_seed_100.pt \
  checkpoints/lambda_sensitivity_003/

run_candidate 001 0.01 1234
run_candidate 003 0.03 1234
run_candidate 020 0.20 42,100,1234
run_candidate 030 0.30 42,100,1234
