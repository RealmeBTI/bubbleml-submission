# Statistical Verification

## Recomputed retained analyses

`scripts/reproduce_reported_results.py` recomputes the tutorial paired values
from retained per-seed JSON and checks the stored figures/results with an
absolute tolerance of `5e-8`.

| Analysis | Sample size | Result verified from retained data |
|---|---:|---|
| Tutorial T-FNO minus U-Net | 11 paired seeds | GWRMSE −0.05698047, exact p=.146484375, Holm=1.0; interface-temperature RMSE −0.50189749, Holm=.03515625; jump MAE −0.43146611, Holm=.021484375; mass MAE +0.04493574, Holm=.021484375 |
| Lambda=.30 divergence hybrid vs U-Net mass MAE | 11 paired seeds | −0.07212217; CI [−0.07939724, −0.06534623]; one-sided sign-flip p=.00048828125; non-inferior under the recorded margin |
| Cross-condition T-FNO minus U-Net | 5 paired seeds | All four reported mean errors favor U-Net directionally; every stored Holm p=1.0, so no confirmatory superiority claim is supported |

The cross-condition summary is compact: individual per-seed rows are unavailable
locally, so its reported means/CIs/p-values were checked for internal presence
and protocol consistency but cannot be independently recomputed from raw rows.
No number was changed in this audit.

`STATISTICAL_VERIFICATION = PASS` within the retained-artifact boundary.
