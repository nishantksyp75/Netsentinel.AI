"""Probability reliability diagnostics for held-out classifier outputs."""
from __future__ import annotations

import numpy as np


def multiclass_reliability(y_true: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> dict:
    """Return ECE, multiclass Brier score, and confidence-bin diagnostics."""
    actual = np.asarray(y_true, dtype=int)
    probs = np.asarray(probabilities, dtype=float)
    predicted = probs.argmax(axis=1)
    confidence = probs.max(axis=1)
    correct = predicted == actual
    one_hot = np.eye(probs.shape[1])[actual]
    brier = float(np.mean(np.sum((probs - one_hot) ** 2, axis=1)))
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    ece = 0.0
    for index in range(bins):
        lower, upper = float(edges[index]), float(edges[index + 1])
        mask = (confidence >= lower) & ((confidence < upper) if index < bins - 1 else (confidence <= upper))
        if not mask.any():
            continue
        count = int(mask.sum())
        mean_confidence = float(confidence[mask].mean())
        accuracy = float(correct[mask].mean())
        ece += (count / len(actual)) * abs(accuracy - mean_confidence)
        rows.append({"lower": lower, "upper": upper, "count": count, "mean_confidence": mean_confidence, "accuracy": accuracy})
    return {"expected_calibration_error": float(ece), "multiclass_brier_score": brier, "confidence_bins": rows}
