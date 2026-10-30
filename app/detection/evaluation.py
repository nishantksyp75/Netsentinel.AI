"""Leakage-safe evaluation helpers for binary intrusion-detection ablations."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def binary_detection_metrics(
    actual_attack: np.ndarray, attack_score: np.ndarray, threshold: float
) -> dict:
    """Evaluate a score where larger values indicate a likely attack."""
    actual = np.asarray(actual_attack, dtype=bool)
    predicted = np.asarray(attack_score, dtype=float) >= threshold
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[False, True]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(
        actual, predicted, average="binary", zero_division=0
    )
    benign_total = tn + fp
    attack_total = tp + fn
    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate_benign": float(fp / benign_total) if benign_total else 0.0,
        "attack_detection_rate": float(tp / attack_total) if attack_total else 0.0,
        "alerts_flagged_fraction": float(predicted.mean()),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def tune_f1_threshold(actual_attack: np.ndarray, attack_score: np.ndarray) -> dict:
    """Select a score threshold using validation data only.

    Ties prefer higher precision, then recall, then the lower threshold.  The
    deterministic grid keeps the experiment reproducible and easy to report.
    """
    candidates = [
        binary_detection_metrics(actual_attack, attack_score, threshold)
        for threshold in np.linspace(0.01, 0.99, 99)
    ]
    return max(
        candidates,
        key=lambda result: (result["f1"], result["precision"], result["recall"], -result["threshold"]),
    )


def fuse_attack_scores(
    supervised_score: np.ndarray,
    anomaly_score: np.ndarray,
    supervised_weight: float = 0.55,
    anomaly_weight: float = 0.25,
) -> np.ndarray:
    """Fuse scores to [0, 1], excluding unavailable evidence/history terms."""
    if supervised_weight <= 0 or anomaly_weight <= 0:
        raise ValueError("Fusion weights must be positive")
    combined = (
        supervised_weight * np.asarray(supervised_score, dtype=float)
        + anomaly_weight * np.asarray(anomaly_score, dtype=float)
    ) / (supervised_weight + anomaly_weight)
    return np.clip(combined, 0.0, 1.0)


def tune_hybrid_fusion(
    actual_attack: np.ndarray, supervised_score: np.ndarray, anomaly_score: np.ndarray
) -> dict:
    """Select hybrid fusion weights and threshold on validation data only."""
    candidates = []
    for supervised_weight in np.linspace(0.10, 0.90, 17):
        anomaly_weight = 1.0 - float(supervised_weight)
        score = fuse_attack_scores(
            supervised_score, anomaly_score, float(supervised_weight), anomaly_weight
        )
        evaluation = tune_f1_threshold(actual_attack, score)
        candidates.append({
            "supervised_weight": float(supervised_weight),
            "anomaly_weight": anomaly_weight,
            "validation": evaluation,
        })
    return max(
        candidates,
        key=lambda item: (
            item["validation"]["f1"],
            item["validation"]["precision"],
            -item["validation"]["false_positive_rate_benign"],
        ),
    )
