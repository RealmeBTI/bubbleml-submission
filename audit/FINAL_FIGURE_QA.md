# Final Figure QA

All six submission figures have PNG, SVG, and PDF forms. The PNG forms were
opened visually; the SVG/PDF companions exist and are non-empty. No NaN/Inf text
or clipping was observed in the rendered PNG review.

| Figure | Result | Evidence |
|---|---|---|
| fig1_pareto_front | PASS | Tutorial split, labeled interface-temperature RMSE and mass-conservation MAE; values agree with retained results. |
| fig2_dry_area_trace | PASS | Explicitly labeled Tutorial Twall-100 rollout; ground truth, T-FNO, U-Net, and threshold are legible. |
| fig3_lambda_sensitivity | PASS | Lambda selection plot uses recorded sweep and labels the tested range. |
| fig4_loss_curves | PASS | Training/validation curves are labeled as recorded runs. |
| fig5_benchmark_workflow | PASS | Contains Dataset → Preprocessing → Training → Evaluation → Statistics → Cross-condition → Artifact release and states the artifact boundary. |
| fig6_split_design | PASS | Separates tutorial 103/106/100 from cross-condition 79/85/90/95, 81, 98/110 roles. |

No prediction-versus-ground-truth field-snapshot figure is claimed or added:
the required compatible arrays/checkpoints are unavailable.
