# BubbleML Resolution Control Experiment: 48x48

## Experiment Overview
This experiment evaluated the U-Net model on the BubbleML dataset downscaled to a **48x48 spatial resolution**. The objective was to test the hardware utilization and physical fidelity of the model at a lower resolution compared to the standard 96x96 and 192x192 resolutions.

- **Environment**: Kaggle (CUDA - Nvidia Tesla T4)
- **Model**: U-Net
- **Number of Seeds**: 11 (Seeds: 7, 17, 42, 100, 314, 1234, 2025, 2718, 4242, 7777, 9999)
- **Parameters**: 7,770,169
- **Device**: CUDA

## Results Summary
The experiment was completed successfully on the Nvidia T4 instance. The aggregated benchmark metrics across all 11 seeds indicate stable convergence and high throughput at this resolution.

### Key Metrics (Average across all 11 seeds)
*   **RMSE**: 8.96
*   **Relative L2**: 0.941
*   **Throughput (windows/second)**: 29.68
*   **Latency (ms/window)**: 33.71
*   **Model Inference Throughput (windows/second)**: 897.5
*   **Model Inference Latency (ms/window)**: 1.19
*   **Mass Conservation MAE**: 0.190
*   **Interface Temperature Jump MAE**: 11.16

## File Locations
All generated results have been successfully preserved and are available in your local repository for independent verification.

- **Experiment Results Directory**: `/Users/sbmahafujbondhon/antigravity_BUbbleML/bubbleml-submission/benchmark_results/resolution_control_48x48/`
- **JSON Aggregation**: `benchmark_results.json` (Contains the detailed nested JSON structure of all metrics)
- **CSV Summary**: `benchmark_summary.csv` (Tabular format for easy analysis)
- **Hardware Profile**: `hardware.txt` (Records the GPU and environment state)
- **Individual Seed Results**: `/Users/sbmahafujbondhon/antigravity_BUbbleML/bubbleml-submission/experiments/resolution_control_48x48/`

*Note: The raw model weights and `loss_curve.png` files for individual seeds are also available in the individual seed directories, and these summarized benchmark files are everything needed for statistical analysis.*
