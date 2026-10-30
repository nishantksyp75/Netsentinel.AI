
import os
import requests
import streamlit as st

API = os.getenv("NETSENTINEL_API", "http://127.0.0.1:8000")
API_KEY = os.getenv("NETSENTINEL_API_KEY", "")


def apply_theme():
    """Shared NetSentinel Cyber SOC dashboard theme."""

    st.markdown("""
    <style>

    /* =====================================
       SIDEBAR FILTER LABELS
    ===================================== */

    [data-testid="stSidebar"] label {
        color: #e5f3ff !important;
        font-weight: 600 !important;
    }

    /* =====================================
       DROPDOWN AND MULTISELECT BACKGROUND
    ===================================== */

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #10283a !important;
        border: 1px solid #1685a5 !important;
        border-radius: 9px !important;
    }

   /* ONLY SELECTED FILTER TAGS - LIGHT CYAN */

    /* SELECTED FILTER TAGS - MUTED LIGHT CYAN */

[data-testid="stSidebar"] [data-baseweb="tag"],
[data-testid="stSidebar"] [data-baseweb="tag"] > span,
[data-testid="stSidebar"] [data-baseweb="tag"] > div {
    background: #A8DCE8 !important;
    background-color: #A8DCE8 !important;
    border: 1px solid #78C6D8 !important;
    border-radius: 6px !important;
}

/* Selected tag text */
[data-testid="stSidebar"] [data-baseweb="tag"] *,
[data-testid="stSidebar"] [data-baseweb="tag"] span {
    color: #061827 !important;
    font-weight: 700 !important;
}

/* Selected tag close icon */
[data-testid="stSidebar"] [data-baseweb="tag"] svg {
    fill: #061827 !important;
    color: #061827 !important;
}
    /* =====================================
       DROPDOWN INPUT TEXT
    ===================================== */

    [data-testid="stSidebar"] [data-baseweb="select"] input {
        color: #ffffff !important;
    }

    /* =====================================
       DROPDOWN OPTIONS
    ===================================== */

    [data-baseweb="popover"],
    [role="listbox"] {
        background-color: #10283a !important;
    }

    [role="option"] {
        background-color: #10283a !important;
        color: #e5f3ff !important;
    }

    [role="option"]:hover {
        background-color: #07536b !important;
        color: #ffffff !important;
    }

    /* =====================================
       SLIDER LABELS AND VALUE
    ===================================== */

    [data-testid="stSidebar"] [data-testid="stSlider"] {
        color: #e5f3ff !important;
    }

    [data-testid="stSidebar"] [data-testid="stSlider"] p {
        color: #e5f3ff !important;
    }

    /* =====================================
       SLIDER THUMB
    ===================================== */

    [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {
        background-color: #0086A8 !important;
        border: 2px solid #ffffff !important;
    }

    /* =====================================
       SLIDER TRACK
    ===================================== */

    [data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] {
        color: #0086A8 !important;
    }

    </style>
    """, unsafe_allow_html=True)


def api(method: str, path: str, **kwargs):
    try:
        headers = kwargs.pop("headers", {})

        if API_KEY:
            headers = {**headers, "X-API-Key": API_KEY}

        response = requests.request(
            method,
            f"{API}{path}",
            timeout=15,
            headers=headers,
            **kwargs
        )

        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
        return None
