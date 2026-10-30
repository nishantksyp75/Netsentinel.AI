from __future__ import annotations

import json, time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             classification_report, confusion_matrix, precision_recall_fscore_support)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from .data import LABEL, numeric_features
from .evaluation import binary_detection_metrics, fuse_attack_scores, tune_f1_threshold, tune_hybrid_fusion
from .reliability import multiclass_reliability
from .splits import three_way_indices

def aligned_probabilities(model: Pipeline, data: pd.DataFrame, n_classes: int) -> np.ndarray:
    """Expand probabilities when a robustness split lacks training examples for a class."""
    probabilities = model.predict_proba(data)
    classes = np.asarray(getattr(model.named_steps["model"], "_netsentinel_global_classes", model.named_steps["model"].classes_), dtype=int)
    if probabilities.shape[1] == n_classes and np.array_equal(classes, np.arange(n_classes)):
        return probabilities
    aligned = np.zeros((len(data), n_classes), dtype=float)
    aligned[:, classes] = probabilities
    return aligned


def global_predictions(model: Pipeline, data: pd.DataFrame) -> np.ndarray:
    predicted = np.asarray(model.predict(data), dtype=int)
    classes = getattr(model.named_steps["model"], "_netsentinel_global_classes", None)
    return np.asarray(classes, dtype=int)[predicted] if classes is not None else predicted

def train_models(data: pd.DataFrame, output_dir: str | Path, seed: int = 42, split_strategy: str = "stratified_random") -> dict:
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    features = numeric_features(data)
    X = data[features].apply(pd.to_numeric, errors="coerce")
    y_raw = data[LABEL].astype(str)
    enc = LabelEncoder(); y = enc.fit_transform(y_raw)
    # Keep the test set untouched until final reporting. Thresholds are chosen
    # only on validation data, preventing optimistic comparisons.
    train_idx, validation_idx, test_idx = three_way_indices(data, y, split_strategy, seed)
    X_train, X_validation, X_test = X.iloc[train_idx], X.iloc[validation_idx], X.iloc[test_idx]
    y_train, y_validation, y_test = y[train_idx], y[validation_idx], y[test_idx]
    prep = ColumnTransformer([("numeric", Pipeline([("impute", SimpleImputer(strategy="median"))]), features)], remainder="drop")
    rf = Pipeline([("prep", prep), ("model", RandomForestClassifier(n_estimators=250, random_state=seed, n_jobs=-1, class_weight="balanced_subsample"))])
    rf.fit(X_train, y_train)
    n_classes = len(enc.classes_)
    xgb_global_classes = np.unique(y_train)
    xgb_train_labels = np.searchsorted(xgb_global_classes, y_train)
    xgb = Pipeline([("prep", prep), ("model", XGBClassifier(n_estimators=250, max_depth=8, learning_rate=.08, subsample=.8, colsample_bytree=.8, objective="multi:softprob", num_class=len(xgb_global_classes), eval_metric="mlogloss", random_state=seed, n_jobs=-1))])
    xgb.fit(X_train, xgb_train_labels)
    xgb.named_steps["model"]._netsentinel_global_classes = xgb_global_classes
    train_labels = y_raw.loc[X_train.index]
    validation_labels = y_raw.loc[X_validation.index]
    test_labels = y_raw.loc[X_test.index]
    benign = X_train[train_labels.str.upper().eq("BENIGN").to_numpy()] if "BENIGN" in enc.classes_ else X_train
    iso = Pipeline([("prep", prep), ("model", IsolationForest(n_estimators=200, contamination="auto", random_state=seed, n_jobs=-1))])
    iso.fit(benign if len(benign) else X_train)
    metrics = {"split": {"seed": seed, "strategy": split_strategy, "train_rows": len(X_train), "validation_rows": len(X_validation), "test_rows": len(X_test), "features": features}, "models": {}}
    for name, model in {"random_forest": rf, "xgboost": xgb}.items():
        started=time.perf_counter(); pred=global_predictions(model, X_test); probabilities=aligned_probabilities(model, X_test, n_classes); latency=(time.perf_counter()-started)/len(X_test)*1000
        p,r,f,_=precision_recall_fscore_support(y_test,pred,average="weighted",zero_division=0)
        macro_p,macro_r,macro_f,_=precision_recall_fscore_support(y_test,pred,average="macro",zero_division=0)
        y_one_hot=np.eye(n_classes)[y_test]
        metrics["models"][name]={"accuracy":accuracy_score(y_test,pred),"balanced_accuracy":balanced_accuracy_score(y_test,pred),"precision_weighted":p,"recall_weighted":r,"f1_weighted":f,"precision_macro":macro_p,"recall_macro":macro_r,"f1_macro":macro_f,"pr_auc_macro":average_precision_score(y_one_hot,probabilities,average="macro"),"pr_auc_weighted":average_precision_score(y_one_hot,probabilities,average="weighted"),"latency_ms_per_flow":latency,"calibration":multiclass_reliability(y_test,probabilities),"per_class":classification_report(y_test,pred,labels=np.arange(n_classes),target_names=enc.classes_,output_dict=True,zero_division=0),"confusion_matrix":confusion_matrix(y_test,pred,labels=np.arange(n_classes)).tolist(),"class_order":enc.classes_.tolist()}
    started=time.perf_counter(); anomaly_pred=(iso.predict(X_test) == -1); anomaly_latency=(time.perf_counter()-started)/len(X_test)*1000
    if "BENIGN" in enc.classes_:
        actual_anomaly=~test_labels.str.upper().eq("BENIGN").to_numpy()
        p,r,f,_=precision_recall_fscore_support(actual_anomaly,anomaly_pred,average="binary",zero_division=0)
        metrics["models"]["isolation_forest"]={"precision_attack_proxy":p,"recall_attack_proxy":r,"f1_attack_proxy":f,"false_positive_rate_benign":float(anomaly_pred[~actual_anomaly].mean()),"anomaly_rate":float(anomaly_pred.mean()),"latency_ms_per_flow":anomaly_latency,"note":"Binary anomaly proxy: every non-BENIGN label is treated as anomalous; this is not multi-class classification."}
        benign_index = int(np.where(enc.classes_ == "BENIGN")[0][0])
        xgb_validation_score = 1.0 - aligned_probabilities(xgb, X_validation, n_classes)[:, benign_index]
        xgb_test_score = 1.0 - aligned_probabilities(xgb, X_test, n_classes)[:, benign_index]
        iso_validation_score = 1.0 / (1.0 + np.exp(5.0 * iso.decision_function(X_validation)))
        iso_test_score = 1.0 / (1.0 + np.exp(5.0 * iso.decision_function(X_test)))
        validation_attack = ~validation_labels.str.upper().eq("BENIGN").to_numpy()

        xgb_validation_choice = tune_f1_threshold(validation_attack, xgb_validation_score)
        iso_validation_choice = tune_f1_threshold(validation_attack, iso_validation_score)
        fixed_hybrid_validation_score = fuse_attack_scores(xgb_validation_score, iso_validation_score)
        fixed_hybrid_validation_choice = tune_f1_threshold(validation_attack, fixed_hybrid_validation_score)
        tuned_fusion = tune_hybrid_fusion(validation_attack, xgb_validation_score, iso_validation_score)
        tuned_hybrid_test_score = fuse_attack_scores(
            xgb_test_score,
            iso_test_score,
            tuned_fusion["supervised_weight"],
            tuned_fusion["anomaly_weight"],
        )
        metrics["hybrid_ablation"] = {
            "protocol": "Binary BENIGN-versus-non-BENIGN ablation. Models fit only on training rows; thresholds and tuned fusion weights are selected exclusively on validation rows; metrics below are a single untouched held-out test evaluation.",
            "fixed_fusion": {"formula": "(0.55 * XGBoost attack score + 0.25 * Isolation Forest anomaly score) / 0.80", "supervised_weight": 0.55, "anomaly_weight": 0.25},
            "validation_tuned_fusion": {"supervised_weight": tuned_fusion["supervised_weight"], "anomaly_weight": tuned_fusion["anomaly_weight"], "threshold": tuned_fusion["validation"]["threshold"], "validation_f1": tuned_fusion["validation"]["f1"]},
            "note": "Evidence and historical-risk terms are unavailable in this offline flow-record benchmark and are excluded from the fusion.",
            "validation_selection": {
                "xgboost_only": xgb_validation_choice,
                "isolation_forest_only": iso_validation_choice,
                "xgboost_plus_isolation_forest_fixed": fixed_hybrid_validation_choice,
                "xgboost_plus_isolation_forest_tuned": tuned_fusion["validation"],
            },
            "held_out_test": {
                "xgboost_only": binary_detection_metrics(actual_anomaly, xgb_test_score, xgb_validation_choice["threshold"]),
                "isolation_forest_only": binary_detection_metrics(actual_anomaly, iso_test_score, iso_validation_choice["threshold"]),
                "xgboost_plus_isolation_forest_fixed": binary_detection_metrics(actual_anomaly, fuse_attack_scores(xgb_test_score, iso_test_score), fixed_hybrid_validation_choice["threshold"]),
                "xgboost_plus_isolation_forest_tuned": binary_detection_metrics(actual_anomaly, tuned_hybrid_test_score, tuned_fusion["validation"]["threshold"]),
            },
        }
    joblib.dump({"random_forest":rf,"xgboost":xgb,"isolation_forest":iso,"label_encoder":enc,"xgb_global_classes":xgb_global_classes.tolist(),"features":features}, output / "detectors.joblib")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
