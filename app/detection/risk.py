from __future__ import annotations
from app.config import RISK_THRESHOLDS, RISK_WEIGHTS

def risk_score(attack_probability: float, anomaly_score: float, evidence_score: float = 0.0, history_score: float = 0.0) -> float:
    values = {"attack": attack_probability, "anomaly": anomaly_score, "evidence": evidence_score, "history": history_score}
    total = sum(RISK_WEIGHTS.values())
    return round(max(0.0, min(1.0, sum(max(0.0, min(1.0, values[k])) * w for k, w in RISK_WEIGHTS.items()) / total)), 4)

def severity(score: float) -> str:
    if not 0 <= RISK_THRESHOLDS["medium"] < RISK_THRESHOLDS["high"] < RISK_THRESHOLDS["critical"] <= 1:
        raise ValueError("Risk thresholds must satisfy 0 <= medium < high < critical <= 1")
    return ("critical" if score >= RISK_THRESHOLDS["critical"] else "high" if score >= RISK_THRESHOLDS["high"]
            else "medium" if score >= RISK_THRESHOLDS["medium"] else "low")
