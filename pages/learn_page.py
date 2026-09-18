"""Learn page — EDUCATE.

A static browse page showing educational cards for all 10 scam tactic types.
No user input or business logic — purely informational.
"""

import streamlit as st

from data.tactics_library import TACTICS_LIBRARY


def render() -> None:
    """Render the Learn page."""
    st.header("📚 Learn: Scam Tactics Explained")
    st.markdown(
        "Scammers use well-known psychological tricks to manipulate people. "
        "Understanding these tactics is the best defence. "
        "Browse the cards below to learn what to watch for."
    )

    st.divider()

    for tactic_id, tactic in TACTICS_LIBRARY.items():
        _render_tactic_card(tactic_id, tactic)
        st.markdown("")  # spacing between cards


def _render_tactic_card(tactic_id: str, tactic: dict) -> None:
    """Render a single educational tactic card using an expander."""
    icon = tactic.get("icon", "⚠️")
    name = tactic.get("name", tactic_id)

    with st.expander(f"{icon}  {name}", expanded=False):
        st.markdown(f"**What it is:**  {tactic['description']}")
        st.markdown("")

        st.markdown(f"**Real-world example:**  {tactic['example']}")
        st.markdown("")

        st.markdown(f"**Warning signs to look for:**  {tactic['warning']}")
        st.markdown("")

        st.markdown(
            f'<div style="'
            f"background-color:#dbeafe; border-radius:6px; "
            f'padding:10px 14px; font-size:0.92rem;">'
            f"💡 <strong>Safe tip:</strong> {tactic['tip']}"
            f"</div>",
            unsafe_allow_html=True,
        )
