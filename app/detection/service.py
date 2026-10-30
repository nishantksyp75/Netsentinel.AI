from __future__ import annotations
from pathlib import Path
import joblib, numpy as np, pandas as pd
from .risk import risk_score, severity

class Detector:
    def __init__(self, model_path: str | Path): self.bundle = joblib.load(model_path)
    def predict(self, features: dict, evidence_score: float=0., history_score: float=0.) -> dict:
        cols=self.bundle["features"]; X=pd.DataFrame([{c: features.get(c) for c in cols}])
        model=self.bundle["xgboost"]; probs=model.predict_proba(X)[0]
        global_classes=np.asarray(self.bundle.get("xgb_global_classes", model.named_steps["model"].classes_), dtype=int)
        idx=int(np.argmax(probs)); global_idx=int(global_classes[idx])
        benign_positions=np.flatnonzero(global_classes == 0)
        attack=float(1-probs[benign_positions[0]]) if len(benign_positions) else 1.0
        anomaly_raw=float(self.bundle["isolation_forest"].decision_function(X)[0]); anomaly=float(1/(1+np.exp(5*anomaly_raw)))
        labels=self.bundle["label_encoder"].inverse_transform([global_idx]); score=risk_score(attack, anomaly, evidence_score, history_score)
        probability_labels=self.bundle["label_encoder"].inverse_transform(global_classes)
        return {"predicted_class":str(labels[0]),"attack_probability":round(attack,4),"anomaly_score":round(anomaly,4),"risk_score":score,"severity":severity(score),"probabilities":{str(k):round(float(v),4) for k,v in zip(probability_labels,probs)}}
