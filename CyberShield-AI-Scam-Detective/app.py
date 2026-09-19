"""AI Scam Detective — Streamlit application entry point.

Handles page configuration, navigation, and session state initialisation.
All page content is delegated to the modules in views/.
"""

import os

import streamlit as st
from dotenv import load_dotenv

from ui.theme import apply_theme

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

apply_theme()

# Keep custom HTML cards readable in both Streamlit light and dark themes.  The
# app uses a few light-coloured educational panels; without explicit foreground
# colours Streamlit's dark-theme text can appear white on those panels.
st.markdown(
    """
    <style>
        .stApp {
            background-color: #071326;
            background-image:
                radial-gradient(circle at 8% 8%, rgba(0, 229, 255, .18), transparent 23rem),
                radial-gradient(circle at 92% 16%, rgba(126, 87, 255, .17), transparent 26rem),
                linear-gradient(135deg, #071326 0%, #0c1f3d 50%, #071326 100%);
        }
        .block-container { max-width: 1000px; padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stSidebar"] { background: #09182d; border-right: 1px solid rgba(74, 222, 255, .22); }
        [data-testid="stSidebar"] * { color: #e8f1ff; }
        h1, h2, h3 { letter-spacing: -.02em; }
        .hero-panel, .step-card, .info-card {
            border: 1px solid rgba(125, 220, 255, .24);
            background: linear-gradient(135deg, rgba(14, 39, 75, .94), rgba(18, 31, 67, .91));
            border-radius: 18px; padding: 22px; box-shadow: 0 16px 40px rgba(0, 0, 0, .20);
            color: #f4f8ff;
        }
        .hero-panel h1, .hero-panel p, .step-card h3, .step-card p, .info-card h3, .info-card p { color: #f4f8ff; }
        .eyebrow { color: #61e6ff; font-size: .78rem; font-weight: 800; letter-spacing: .11em; text-transform: uppercase; }
        .step-number { color: #61e6ff; font-weight: 800; font-size: 1.15rem; }
        .stButton > button { border-radius: 10px; min-height: 2.7rem; font-weight: 700; }
        [data-testid="stMetric"] { background: rgba(13, 35, 68, .80); border: 1px solid rgba(125, 220, 255, .16); border-radius: 12px; padding: 10px; }
        .scam-card { color: #172033; }
        .scam-card p, .scam-card li, .scam-card span { color: #172033; }
        .scam-card a { color: #0b57d0; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
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
if "detective_scored_ids" not in st.session_state:
    st.session_state["detective_scored_ids"] = set()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🕵️ AI Scam Detective")
    st.caption("A cybersecurity awareness tool")
    st.divider()

    with st.expander("🔑 Set up free AI analysis"):
        st.markdown("1. Create a free key in [Google AI Studio](https://aistudio.google.com/app/apikey).")
        st.markdown("2. Copy `.env.example` to a new file named `.env`.")
        st.markdown("3. Paste the key after `GEMINI_API_KEY=` and restart the app.")
        st.caption("Free-tier quota is limited. Your key stays on your computer and is never shown in this app.")

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
    from views.analyze_page import render
    render()

elif page == "🕵️ Detective Mode":
    from views.detective_page import render
    render()

elif page == "📚 Learn":
    from views.learn_page import render
    render()
