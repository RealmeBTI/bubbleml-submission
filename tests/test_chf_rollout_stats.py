from __future__ import annotations

import json

from bubbleml_benchmark.chf_rollout_stats import CHFRolloutStatisticsConfig, run


def _result(seed: int, tfno: float, unet: float) -> dict[str, object]:
    endpoint = {"rmse": 1.0, "gwrmse": 2.0, "mass_conservation_mae": 0.1}
    return {
        "source": {"autoregressive_steps": 164},
        "signals": {"ground_truth": [0.0, 0.2], "tfno": [tfno, 0.2], "unet": [unet, 0.2]},
        "events": {"tfno": {"frames_at_or_above_threshold": 4}, "unet": {"frames_at_or_above_threshold": 1}},
        "horizon_metrics": {"tfno": {"164": endpoint}, "unet": {"164": endpoint}},
        "provenance": {"tfno": {"checkpoint_seed": seed}, "unet": {"checkpoint_seed": seed}},
    }


def test_rollout_statistics_reuses_paired_inference(tmp_path) -> None:
    for seed, tfno, unet in ((42, 0.4, 0.1), (100, 0.3, 0.0)):
        destination = tmp_path / f"seed_{seed}"
        destination.mkdir()
        (destination / "rollout_results.json").write_text(json.dumps(_result(seed, tfno, unet)))

    output = tmp_path / "statistics.json"
    result = run(
        CHFRolloutStatisticsConfig(
            results_dir=str(tmp_path), output_path=str(output), seeds=(42, 100), bootstrap_samples=10
        )
    )

    assert output.is_file()
    comparison = result["paired_tfno_minus_unet"]
    assert comparison["cumulative_dry_area_mae"]["mean_fno_minus_unet"] > 0
    assert comparison["false_alarm_frame_count"]["mean_fno_minus_unet"] == 3.0
