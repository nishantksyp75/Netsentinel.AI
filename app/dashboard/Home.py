
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dashboard.common import api, apply_theme

st.set_page_config(
    page_title="NetSentinel AI | SOC",
    page_icon="🛡️",
    layout="wide"
)

apply_theme()

# HEADER
st.markdown("""
<div style="
    background:linear-gradient(110deg,#09263b,#0b3b55,#071b2d);
    border:1px solid #087d9d;
    border-radius:15px;
    padding:25px;
    margin-bottom:22px;
    box-shadow:0 0 22px rgba(0,213,255,.12);
">
    <div style="color:#4ce2ff;font-size:13px;font-weight:700;letter-spacing:3px">
        NETSENTINEL.AI  /  SECURITY OPERATIONS CENTER
    </div>
    <div style="color:white;font-size:32px;font-weight:800;margin-top:8px">
        Threat Intelligence Dashboard
    </div>
    <div style="color:#a9c9dd;font-size:14px;margin-top:7px">
        Explainable Intrusion Detection • Human-Approved Investigation
    </div>
</div>
""", unsafe_allow_html=True)

alerts = api("GET", "/alerts") or []
frame = pd.DataFrame(alerts)

if not frame.empty:
    for col, default in {
        "severity": "unknown",
        "status": "unknown",
        "predicted_class": "unknown",
        "risk_score": 0
    }.items():
        if col not in frame.columns:
            frame[col] = default

    frame["risk_score"] = pd.to_numeric(
        frame["risk_score"], errors="coerce"
    ).fillna(0)

    high = int(
        frame["severity"].astype(str).str.lower()
        .isin(["high", "critical"]).sum()
    )
    open_count = int(
        frame["status"].astype(str).str.lower().eq("open").sum()
    )
    avg_risk = frame["risk_score"].mean()
    classes = frame["predicted_class"].nunique()
else:
    high = open_count = classes = 0
    avg_risk = 0

# METRIC CARDS
st.markdown("### ◈ SECURITY OVERVIEW")

c1, c2, c3, c4 = st.columns(4)

cards = [
    (c1, "TOTAL ALERTS", len(alerts), "#19c8f2"),
    (c2, "HIGH / CRITICAL", high, "#ff526b"),
    (c3, "OPEN ALERTS", open_count, "#ffb84d"),
    (c4, "AVERAGE RISK", f"{avg_risk:.3f}", "#42dfaa"),
]

for col, label, value, accent in cards:
    with col:
        st.markdown(f"""
        <div style="
            background:linear-gradient(145deg,#102c40,#091b2b);
            border:1px solid {accent};
            border-left:4px solid {accent};
            border-radius:12px;
            padding:20px;
            min-height:112px;
            box-shadow:0 0 15px {accent}20;
        ">
            <div style="color:{accent};font-size:12px;font-weight:700;
                        letter-spacing:1px">{label}</div>
            <div style="color:white;font-size:32px;font-weight:800;
                        margin-top:10px">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# CHARTS
left, right = st.columns([1, 1])

with left:
    st.markdown("### ◈ THREAT SEVERITY")
    if not frame.empty:
        severity_counts = (
            frame["severity"].astype(str).str.upper()
            .value_counts()
        )
        st.bar_chart(severity_counts, color="#00c8ef")
    else:
        st.info("No severity data available.")

with right:
    st.markdown("### ◈ DETECTION CLASSES")
    if not frame.empty:
        class_counts = frame["predicted_class"].value_counts().head(8)
        st.bar_chart(class_counts, color="#36d6a2")
    else:
        st.info("No detection data available.")

st.divider()

# RECENT ALERTS
st.markdown("### ◈ RECENT SECURITY EVENTS")

if not frame.empty:
    display_cols = [
        col for col in [
            "id", "severity", "predicted_class",
            "status", "risk_score"
        ] if col in frame.columns
    ]

    recent = frame[display_cols].head(10).copy()

    st.dataframe(
        recent.style
        .map(
            lambda x: (
                "color:#ff647b;font-weight:bold"
                if str(x).lower() in ["critical", "high"]
                else "color:#ffc66d;font-weight:bold"
                if str(x).lower() == "medium"
                else "color:#55dfb0;font-weight:bold"
            ),
            subset=["severity"]
        )
        .bar(subset=["risk_score"], vmin=0, vmax=1, color="#087da8")
        .format({"risk_score": "{:.3f}"}),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No persisted alerts yet.")

# SAFETY BOUNDARY
st.markdown("""
<div style="
    background:#10283a;
    border:1px solid #16728b;
    border-radius:12px;
    padding:18px;
    margin-top:20px;
">
    <div style="color:#4ce2ff;font-weight:700">
        ◈ INVESTIGATION SAFETY BOUNDARY
    </div>
    <p style="color:#b6ccdc;margin-bottom:0">
        NetSentinel retrieves defensive evidence and knowledge.
        It cannot make network changes. An analyst must approve
        or reject every recommendation.
    </p>
</div>
""", unsafe_allow_html=True)
