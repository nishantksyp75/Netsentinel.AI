
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dashboard.common import api, apply_theme

apply_theme()

st.title("🛡️ Alerts & Threat Evidence")
st.caption("NETWORK THREAT MONITORING  |  DETECTION & ANALYSIS")

alerts = api("GET", "/alerts") or []

if not alerts:
    st.info("No alerts stored yet. Score a network flow or create a test alert.")
    st.stop()

frame = pd.DataFrame(alerts)

# Ensure expected columns exist
for col, default in {
    "severity": "unknown",
    "predicted_class": "unknown",
    "status": "unknown",
    "risk_score": 0.0,
    "attack_probability": 0.0,
    "anomaly_score": 0.0,
}.items():
    if col not in frame.columns:
        frame[col] = default

for col in ["risk_score", "attack_probability", "anomaly_score"]:
    frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)

# ===== FILTERS =====
with st.sidebar:
    st.markdown("## ◈ FILTER ALERTS")

    severity_options = sorted(frame["severity"].dropna().unique().tolist())
    class_options = sorted(frame["predicted_class"].dropna().unique().tolist())
    status_options = sorted(frame["status"].dropna().unique().tolist())

    severity_filter = st.multiselect(
        "Severity",
        severity_options,
        default=severity_options
    )

    class_filter = st.multiselect(
        "Predicted class",
        class_options,
        default=class_options
    )

    status_filter = st.multiselect(
        "Status",
        status_options,
        default=status_options
    )

    minimum_risk = st.slider(
        "Minimum risk score",
        0.0, 1.0, 0.0, 0.05
    )

filtered = frame[
    frame["severity"].isin(severity_filter)
    & frame["predicted_class"].isin(class_filter)
    & frame["status"].isin(status_filter)
    & (frame["risk_score"] >= minimum_risk)
].copy()

# ===== METRICS =====
high_count = int(
    filtered["severity"].astype(str).str.lower()
    .isin(["high", "critical"]).sum()
)

unique_classes = filtered["predicted_class"].nunique()
average_risk = filtered["risk_score"].mean() if len(filtered) else 0

st.markdown("### ◈ THREAT OVERVIEW")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("▣ MATCHING ALERTS", len(filtered))

with c2:
    st.metric("⚠ HIGH SEVERITY", high_count)

with c3:
    st.metric("⬡ UNIQUE CLASSES", unique_classes)

with c4:
    st.metric("◉ AVG RISK SCORE", f"{average_risk:.3f}")

st.divider()

# ===== ALERT TABLE =====
st.markdown("### ◈ LIVE SECURITY ALERTS")
st.caption("Filtered network events with model risk indicators")

if filtered.empty:
    st.warning("No alerts match the selected filters.")
    st.stop()

display_columns = [
    col for col in [
        "id",
        "created_at",
        "status",
        "predicted_class",
        "attack_probability",
        "anomaly_score",
        "risk_score",
        "severity",
    ]
    if col in filtered.columns
]

table = filtered[display_columns].copy()

def severity_style(value):
    value = str(value).lower()
    if value == "critical":
        return "background-color: #641b2b; color: #ff8292; font-weight: bold"
    if value == "high":
        return "background-color: #51202b; color: #ff9aa8; font-weight: bold"
    if value == "medium":
        return "background-color: #493819; color: #ffd27a; font-weight: bold"
    return "background-color: #123b35; color: #65e6bb"

def status_style(value):
    value = str(value).lower()
    if value == "open":
        return "color: #ff8b8b; font-weight: bold"
    if value == "approved":
        return "color: #56dcae; font-weight: bold"
    return "color: #66caff"

styler = table.style

if "severity" in table.columns:
    styler = styler.map(severity_style, subset=["severity"])

if "status" in table.columns:
    styler = styler.map(status_style, subset=["status"])

for col in ["attack_probability", "anomaly_score", "risk_score"]:
    if col in table.columns:
        styler = styler.bar(
            subset=[col],
            vmin=0,
            vmax=1,
            color="#087da8"
        ).format({col: "{:.3f}"})

st.dataframe(
    styler,
    use_container_width=True,
    hide_index=True,
    height=390
)

# ===== DOWNLOAD =====
st.download_button(
    "⇩ Download filtered alerts as JSON",
    data=json.dumps(
        filtered.to_dict(orient="records"),
        default=str,
        indent=2
    ),
    file_name="netsentinel_filtered_alerts.json",
    mime="application/json"
)

st.divider()

# ===== ALERT DETAILS =====
st.markdown("### ◈ ALERT INVESTIGATION")

choices = {
    f"{a.get('id')} | {a.get('severity')} | {a.get('predicted_class')} | {a.get('status')}": a
    for a in filtered.to_dict(orient="records")
}

selected_label = st.selectbox("Select an alert", list(choices))
selected = choices[selected_label]

with st.expander("View complete alert details", expanded=True):
    st.json(selected)

if st.button("⚡ Start Controlled Investigation", type="primary"):
    result = api("POST", f"/investigate/{selected['id']}")
    if result:
        st.session_state["investigation"] = result
        st.success(f"Investigation {result['id']} created successfully.")

evidence = api("GET", f"/alerts/{selected['id']}/explanation")

if evidence:
    st.markdown("### ◈ MODEL EVIDENCE")
    st.json(evidence)
