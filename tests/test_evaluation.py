import numpy as np

from app.detection.evaluation import binary_detection_metrics, fuse_attack_scores, tune_f1_threshold, tune_hybrid_fusion


def test_binary_metrics_and_validation_threshold_are_deterministic():
    actual = np.array([False, False, True, True])
    score = np.array([0.05, 0.30, 0.70, 0.95])
    chosen = tune_f1_threshold(actual, score)
    metrics = binary_detection_metrics(actual, score, chosen["threshold"])
    assert metrics["f1"] == 1.0
    assert metrics["false_positive_rate_benign"] == 0.0


def test_fusion_is_normalized():
    fused = fuse_attack_scores(np.array([1.0, 0.0]), np.array([1.0, 0.0]))
    assert np.allclose(fused, [1.0, 0.0])


def test_tuned_fusion_uses_validation_metrics():
    actual = np.array([False, False, True, True])
    result = tune_hybrid_fusion(actual, np.array([0.1, 0.2, 0.8, 0.9]), np.array([0.2, 0.1, 0.7, 0.8]))
    assert result["validation"]["f1"] == 1.0
    assert result["supervised_weight"] + result["anomaly_weight"] == 1.0
