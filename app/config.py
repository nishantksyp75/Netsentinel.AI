from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(os.getenv("MODEL_DIR", ROOT / "models"))
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", ROOT / "data" / "knowledge"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'netsentinel.db'}")
MAX_RELATED_ALERTS = int(os.getenv("MAX_RELATED_ALERTS", "20"))
API_KEY = os.getenv("NETSENTINEL_API_KEY", "")
RATE_LIMIT_PER_MINUTE = int(os.getenv("NETSENTINEL_RATE_LIMIT_PER_MINUTE", "0"))
RISK_WEIGHTS = {k: float(os.getenv(env, default)) for k, env, default in [
    ("attack", "RISK_ATTACK_WEIGHT", "0.55"), ("anomaly", "RISK_ANOMALY_WEIGHT", "0.25"),
    ("evidence", "RISK_EVIDENCE_WEIGHT", "0.15"), ("history", "RISK_HISTORY_WEIGHT", "0.05"),
]}
RISK_THRESHOLDS = {
    "medium": float(os.getenv("RISK_MEDIUM_THRESHOLD", "0.35")),
    "high": float(os.getenv("RISK_HIGH_THRESHOLD", "0.65")),
    "critical": float(os.getenv("RISK_CRITICAL_THRESHOLD", "0.85")),
}
