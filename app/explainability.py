from __future__ import annotations
import numpy as np
from app.detection.service import Detector

def feature_evidence(detector: Detector, flow: dict, top_k: int=8) -> list[dict]:
    """Return stable, serializable feature evidence for dashboard/API use.

    Global RF importances provide a safe fallback when SHAP is unavailable.
    The returned evidence identifies the method used.
    """
    rf=detector.bundle["random_forest"].named_steps["model"]
    names=detector.bundle["features"]; importance=np.asarray(rf.feature_importances_)
    items=sorted(zip(names,importance),key=lambda x:x[1],reverse=True)[:top_k]
    return [{"feature":name,"observed_value":flow.get(name),"importance":round(float(value),6),"method":"random_forest_global_importance"} for name,value in items]
