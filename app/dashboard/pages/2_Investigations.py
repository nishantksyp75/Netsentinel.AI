
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dashboard.common import api, apply_theme

apply_theme()

# ===== HEADER =====
st.markdown("""
<div style="
    background:linear-gradient(110deg,#09263b,#0b3b55,#071b2d);
    border:1px solid #087d9d;
    border-radius:14px;
    padding:22px;
    margin-bottom:22px;
">
    <div style="color:#45dfff;font-size:12px;font-weight:700;
                letter-spacing:2px">SECURITY OPERATIONS CENTER</div>
    <div style="color:white;font-size:29px;font-weight:800;margin-top:8px">
        ◈ Investigation Command Center
    </div>
    <div style="color:#a9c9dd;margin-top:6px">
        Evidence Analysis | Analyst Review | Human Approval Workflow
    </div>
</div>
""", unsafe_allow_html=True)

# ===== INVESTIGATION DATA =====
result = st.session_state.get("investigation")

if not result:
    st.info("No active investigation. Create an investigation from the Alerts page first.")
    st.stop()

investigation_id = result.get("id", "Unknown")
summary = result.get("summary", "No summary available")
recommendation = result.get("recommendation", "No recommendation available")
trace = result.get("trace", {})
sources = result.get("sources", {})
actions = result.get("analyst_actions", [])

# ===== STATUS CARDS =====
st.markdown("### ◈ INVESTIGATION OVERVIEW")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div style="background:#102b40;border:1px solid #08c7ef;
    border-radius:11px;padding:17px;border-left:4px solid #08c7ef">
        <div style="color:#45dfff;font-size:12px;font-weight:700">
        INVESTIGATION ID</div>
        <div style="color:white;font-size:19px;font-weight:700;
        margin-top:10px;word-break:break-all">{investigation_id}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div style="background:#102b40;border:1px solid #ffb84d;
    border-radius:11px;padding:17px;border-left:4px solid #ffb84d">
        <div style="color:#ffbd59;font-size:12px;font-weight:700">
        REVIEW STATUS</div>
        <div style="color:white;font-size:21px;font-weight:700;
        margin-top:10px">PENDING REVIEW</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div style="background:#102b40;border:1px solid #42dfaa;
    border-radius:11px;padding:17px;border-left:4px solid #42dfaa">
        <div style="color:#42dfaa;font-size:12px;font-weight:700">
        ANALYST ACTIONS</div>
        <div style="color:white;font-size:21px;font-weight:700;
        margin-top:10px">{len(actions)}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ===== SUMMARY =====
st.markdown("### ◈ INVESTIGATION SUMMARY")

st.markdown(f"""
<div style="background:#0c2233;border:1px solid #174b65;
border-radius:11px;padding:19px;color:#dceeff">
{summary}
</div>
""", unsafe_allow_html=True)

# ===== RECOMMENDATION =====
st.markdown("### ⚠ DEFENSIVE RECOMMENDATION")

st.warning(recommendation)

# ===== EVIDENCE AND SOURCES =====
st.markdown("### ◈ EVIDENCE INTELLIGENCE")

tab1, tab2 = st.tabs(["Evidence Trace", "Retrieved Defensive Context"])

with tab1:
    st.json(trace)

with tab2:
    st.json(sources)

# ===== ANALYST ACTIONS =====
st.markdown("### ◈ RECOMMENDED ANALYST ACTIONS")

if actions:
    st.dataframe(
        pd.DataFrame(actions),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No analyst actions are available for this investigation.")

st.divider()

# ===== HUMAN APPROVAL =====
st.markdown("### ◈ HUMAN APPROVAL CONTROL")

st.markdown("""
<div style="background:#10283a;border:1px solid #17617a;
border-radius:10px;padding:15px;margin-bottom:15px">
    <span style="color:#45dfff;font-weight:700">
    ANALYST AUTHORIZATION REQUIRED
    </span>
    <p style="color:#b6ccdc;margin-bottom:0">
    Review the evidence and recommendation before recording
    an approval or rejection decision.
    </p>
</div>
""", unsafe_allow_html=True)

comment = st.text_area(
    "Analyst comment",
    placeholder="Enter your investigation findings or decision rationale..."
)

c1, c2 = st.columns(2)

with c1:
    if st.button("✓ APPROVE RECOMMENDATION", type="primary",
                 use_container_width=True):
        response = api(
            "POST",
            f"/incidents/{investigation_id}/decision",
            json={"decision": "approved", "comment": comment}
        )
        if response is not None:
            st.success("Approval decision submitted.")
            st.session_state.pop("investigation", None)

with c2:
    if st.button("✕ REJECT RECOMMENDATION",
                 use_container_width=True):
        response = api(
            "POST",
            f"/incidents/{investigation_id}/decision",
            json={"decision": "rejected", "comment": comment}
        )
        if response is not None:
            st.success("Rejection decision submitted.")
            st.session_state.pop("investigation", None)

st.caption(
    "NetSentinel AI | Human-in-the-loop security investigation"
)
