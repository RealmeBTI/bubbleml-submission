# Figure Quality Audit

Audit date: 2026-08-04.

Each generated line-art figure is supplied as vector PDF and SVG plus a 600 dpi
PNG. Vector files are the preferred submission versions. All four families were
rasterized at reduced size and inspected for readable labels, non-overlapping
legends, and visible markers.

| Figure family | Evidence source | Output dimensions/status |
|---|---|---|
| `fig1_pareto_front` | Stored tutorial and lambda-sensitivity result JSON | PDF/SVG; PNG 6000 x 4000; ready |
| `fig2_dry_area_trace` | Stored Phase 4 rollout series | PDF/SVG; PNG 6000 x 4000; ready |
| `fig3_lambda_sensitivity` | Stored lambda-sensitivity results | PDF/SVG; PNG 9000 x 3000; ready |
| `fig4_loss_curves` | Available stored experiment histories | PDF/SVG; PNG 7500 x 5500; ready |

The requested ground-truth-versus-prediction field-snapshot figure is not in this
package because the necessary cross-condition arrays/checkpoints were not
available. It is explicitly marked as missing rather than synthesized.
