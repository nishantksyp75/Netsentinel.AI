import sys
from pathlib import Path
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.dashboard.common import api, apply_theme

st.title("Agentic AI investigation")
apply_theme()

st.caption("A controlled, read-only analyst assistant. It retrieves evidence and recommends actions; it cannot change network systems.")
alerts = api("GET", "/alerts") or []
if not alerts:
    st.info("No alerts are available. Score a flow or create a test alert first.")
    st.stop()

options = {f"{a['id']} | {a['severity']} | {a['predicted_class']} | risk {a['risk_score']:.2f}": a for a in alerts}
selected = options[st.selectbox("Select alert for investigation", list(options))]
st.subheader("Selected alert")
st.json({key: selected[key] for key in ("id", "predicted_class", "attack_probability", "anomaly_score", "risk_score", "severity", "status")})

if st.button("Run agentic investigation", type="primary"):
    with st.status("Running controlled investigation", expanded=True) as status:
        st.write("Retrieving the structured alert and model evidence")
        investigation = api("POST", f"/investigate/{selected['id']}")
        st.write("Ranking persisted similar cases")
        similar = api("GET", f"/alerts/{selected['id']}/similar-cases")
        status.update(label="Investigation complete", state="complete")
    if investigation:
        st.session_state["agentic_investigation"] = investigation
        st.session_state["agentic_similar_cases"] = (similar or {}).get("cases", [])

result = st.session_state.get("agentic_investigation")
if result:
    st.subheader("Agent conclusion")
    st.write(result["summary"])
    st.warning(result["recommendation"])
    st.subheader("Recommended actions for the analyst")
    st.dataframe(pd.DataFrame(result.get("analyst_actions", [])), hide_index=True)
    st.subheader("Analyst decision")
    with st.form(f"decision_{result['id']}"):
        decision=st.selectbox("Decision", ["approved", "rejected"], key=f"decision_choice_{result['id']}")
        rationale=st.text_area("Analyst rationale", placeholder="State why the recommendation is approved or rejected.", key=f"decision_rationale_{result['id']}")
        submitted=st.form_submit_button("Record decision")
    if submitted:
        recorded=api("POST", f"/incidents/{result['id']}/decision", json={"decision":decision,"comment":rationale})
        if recorded:
            st.success(f"Decision recorded: {recorded['decision']}")
    timeline=api("GET", f"/investigations/{result['id']}/timeline")
    if timeline:
        st.subheader("Investigation timeline")
        st.dataframe(pd.DataFrame(timeline["events"]), hide_index=True)
    st.subheader("Related similar cases")
    cases = st.session_state.get("agentic_similar_cases", [])
    if cases:
        st.dataframe(pd.DataFrame(cases), hide_index=True)
    else:
        st.info("No comparable persisted case was found yet.")
    st.subheader("Evidence tools used")
    st.json(result["trace"])
    st.subheader("Retrieved defensive context")
    st.json(result["sources"])
