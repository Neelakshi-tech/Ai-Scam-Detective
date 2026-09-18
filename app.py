"""AI Scam Detective — Streamlit application entry point.

Handles page configuration, navigation, and session state initialisation.
All page content is delegated to the modules in pages/.
"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Scam Detective",
    page_icon="🕵️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "analyze_result" not in st.session_state:
    st.session_state["analyze_result"] = None
if "analyze_input_text" not in st.session_state:
    st.session_state["analyze_input_text"] = ""
if "detective_result" not in st.session_state:
    st.session_state["detective_result"] = None
if "detective_score_total" not in st.session_state:
    st.session_state["detective_score_total"] = 0
if "detective_challenges_done" not in st.session_state:
    st.session_state["detective_challenges_done"] = 0

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🕵️ AI Scam Detective")
    st.caption("A cybersecurity awareness tool")
    st.divider()

    page = st.radio(
        "Navigate to:",
        options=["🔍 Analyze a Message", "🕵️ Detective Mode", "📚 Learn"],
        key="main_nav",
    )

    st.divider()

    # Session score summary
    done = st.session_state.get("detective_challenges_done", 0)
    if done > 0:
        total = st.session_state.get("detective_score_total", 0)
        avg = round(total / done)
        st.markdown("**🏅 Detective Progress**")
        st.markdown(f"Challenges: **{done}**")
        st.markdown(f"Average score: **{avg}/100**")
        st.divider()

    # API key status indicator
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key != "your_gemini_api_key_here":
        st.success("✅ AI analysis active", icon=None)
    else:
        st.warning(
            "⚠️ No API key found. Running in fallback mode. "
            "Add your Gemini API key to `.env` to enable full AI analysis.",
            icon=None,
        )

    st.divider()
    st.caption(
        "This tool is for educational awareness only. "
        "It does not store your messages or constitute security advice."
    )

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------

# Lazy imports keep startup fast and avoid circular import issues
if page == "🔍 Analyze a Message":
    from pages.analyze_page import render
    render()

elif page == "🕵️ Detective Mode":
    from pages.detective_page import render
    render()

elif page == "📚 Learn":
    from pages.learn_page import render
    render()
