"""Shared visual theme for both the main app and Streamlit's direct page routes."""

import streamlit as st


def apply_theme() -> None:
    """Apply the cyber-security visual system after page configuration."""
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #030817;
                background-image:
                    linear-gradient(rgba(57, 213, 255, .045) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(57, 213, 255, .045) 1px, transparent 1px),
                    radial-gradient(circle at 8% 8%, rgba(0, 229, 255, .20), transparent 24rem),
                    radial-gradient(circle at 92% 16%, rgba(137, 92, 255, .18), transparent 27rem),
                    linear-gradient(135deg, #030817 0%, #071a38 52%, #030817 100%);
                background-size: 32px 32px, 32px 32px, auto, auto, auto;
                background-attachment: fixed;
            }
            .block-container { max-width: 1040px; padding-top: 2rem; padding-bottom: 3rem; }
            header[data-testid="stHeader"] { background: transparent; }
            [data-testid="stSidebar"] {
                background-image: linear-gradient(180deg, rgba(5, 21, 46, .98), rgba(7, 11, 30, .98));
                border-right: 1px solid rgba(74, 222, 255, .25);
            }
            [data-testid="stSidebar"] * { color: #e8f1ff; }
            [data-testid="stSidebar"] .stRadio label { border-radius: 10px; padding: 5px 8px; }
            h1, h2, h3 { letter-spacing: -.02em; }
            h1 { text-shadow: 0 0 24px rgba(97, 230, 255, .18); }
            .hero-panel, .step-card, .info-card {
                border: 1px solid rgba(125, 220, 255, .28);
                background: linear-gradient(135deg, rgba(8, 36, 73, .95), rgba(16, 21, 57, .94));
                border-radius: 18px; padding: 22px; box-shadow: 0 16px 42px rgba(0, 0, 0, .30), inset 0 1px rgba(255,255,255,.05);
                color: #f4f8ff;
            }
            .hero-panel { position: relative; overflow: hidden; border-color: rgba(99, 236, 255, .45); }
            .hero-panel:after { content: ""; position: absolute; right: -55px; top: -75px; width: 210px; height: 210px; border: 1px solid rgba(97, 230, 255, .23); border-radius: 50%; box-shadow: 0 0 0 26px rgba(97, 230, 255, .035), 0 0 0 54px rgba(97, 230, 255, .025); }
            .hero-panel h1, .hero-panel p, .step-card h3, .step-card p, .info-card h3, .info-card p { color: #f4f8ff; }
            .eyebrow { color: #61e6ff; font-size: .78rem; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
            .hero-meta { color: #9defff; font-size: .84rem; font-weight: 700; margin-top: 14px; }
            .step-number { color: #61e6ff; font-weight: 800; font-size: 1.15rem; }
            .step-card { min-height: 150px; transition: transform .18s ease, border-color .18s ease; }
            .step-card:hover { transform: translateY(-3px); border-color: rgba(97, 230, 255, .65); }
            .stButton > button { border-radius: 10px; min-height: 2.7rem; font-weight: 700; letter-spacing: .01em; }
            .stButton > button[kind="primary"] { box-shadow: 0 0 22px rgba(0, 205, 255, .22); }
            [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] div[data-baseweb="select"] > div { border-radius: 10px; }
            [data-testid="stExpander"] { border: 1px solid rgba(108, 213, 255, .20); border-radius: 12px; background: rgba(7, 24, 51, .48); }
            [data-testid="stAlert"] { border-radius: 12px; }
            [data-testid="stMetric"] { background: rgba(13, 35, 68, .80); border: 1px solid rgba(125, 220, 255, .16); border-radius: 12px; padding: 10px; }
            .scam-card { color: #172033; }
            .scam-card p, .scam-card li, .scam-card span { color: #172033; }
            .scam-card a { color: #0b57d0; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )
