"""Learn page — EDUCATE.

A static browse page showing educational cards for all 10 scam tactic types.
No user input or business logic — purely informational.
"""

import streamlit as st

from data.tactics_library import TACTICS_LIBRARY


def render() -> None:
    """Render the Learn page."""
    st.markdown(
        """
        <div class="hero-panel">
            <div class="eyebrow">Build your cyber safety instincts</div>
            <h1 style="margin:6px 0;">📚 Learn scam tactics</h1>
            <p>Each short lesson explains one common trick, gives an example, and shows what to do instead.</p>
            <div class="hero-meta">● KNOW THE PATTERN &nbsp;&nbsp; • &nbsp;&nbsp; PAUSE BEFORE YOU CLICK &nbsp;&nbsp; • &nbsp;&nbsp; STAY IN CONTROL</div>
        </div>
        """, unsafe_allow_html=True,
    )

    st.markdown("### The three rules to remember")
    rule_one, rule_two, rule_three = st.columns(3)
    rule_one.markdown("**🛑 Pause**\n\nUrgency is a common manipulation tactic.")
    rule_two.markdown("**🔎 Verify**\n\nUse the official app, website, or phone number.")
    rule_three.markdown("**🔒 Protect**\n\nNever share an OTP, PIN, password, or card CVV.")

    st.markdown("### Explore the warning signs")
    st.caption("Open any card below. Start with the tactic you see most often in messages you receive.")

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
            f'<div class="scam-card" style="'
            f"background-color:#dbeafe; border-radius:6px; "
            f'padding:10px 14px; font-size:0.92rem;">'
            f"💡 <strong>Safe tip:</strong> {tactic['tip']}"
            f"</div>",
            unsafe_allow_html=True,
        )


# Make Streamlit's automatic /learn_page route render actual content.
if __name__ == "__main__":
    st.set_page_config(page_title="Learn | AI Scam Detective", page_icon="📚", layout="centered")
    from ui.theme import apply_theme

    apply_theme()
    render()
