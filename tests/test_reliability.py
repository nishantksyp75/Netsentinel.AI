import numpy as np

from app.detection.reliability import multiclass_reliability


def test_reliability_reports_perfect_confidence_correctly():
    metrics = multiclass_reliability(
        np.array([0, 1]), np.array([[1.0, 0.0], [0.0, 1.0]])
    )
    assert metrics["expected_calibration_error"] == 0.0
    assert metrics["multiclass_brier_score"] == 0.0
    assert metrics["confidence_bins"][0]["count"] == 2
