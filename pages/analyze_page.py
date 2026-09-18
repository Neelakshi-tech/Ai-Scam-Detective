"""Analyze page — DETECT + EXPLAIN.

The user pastes a suspicious message here, submits it for analysis,
and receives a structured risk assessment.
"""

import streamlit as st

from ai.ai_analyzer import AIAnalyzer
from services.analysis_service import AnalysisService
from ui.components import (
    render_actions,
    render_disclaimer,
    render_fallback_notice,
    render_highlighted_message,
    render_learn_card,
    render_risk_badge,
    render_risk_summary,
    render_tactic_cards,
)

# ---------------------------------------------------------------------------
# Demo messages for easy testing / hackathon demo
# ---------------------------------------------------------------------------

DEMO_MESSAGES = {
    "Select a demo…": "",
    "🚚 Parcel Delivery Scam": (
        "Royal Mail: Your parcel could not be delivered today. "
        "A redelivery fee of £2.99 is required within 24 hours or your parcel "
        "will be returned to sender. Pay immediately at: royalm4il-delivery-fees.com. "
        "Failure to pay will result in a £15 storage charge."
    ),
    "💼 Fake Job Offer": (
        "Hi! We found your CV on Indeed and would love to offer you a work-from-home position "
        "earning up to £800 per day. No experience needed — full training provided. "
        "To secure your spot, send a one-time registration fee of £49 via PayPal "
        "and provide your bank account details for payroll setup. Offer expires tonight!"
    ),
    "🏦 Bank Impersonation": (
        "URGENT: Barclays Security Team — Unusual activity has been detected on your account. "
        "Your account has been temporarily suspended to protect you. "
        "To restore access, verify your identity at: barclays-secure-verify.net "
        "You will need your card number, PIN, and the one-time passcode sent to your phone. "
        "If you do not verify within 2 hours your account will be permanently closed."
    ),
    "🎁 Prize Winner Scam": (
        "Congratulations! You have been selected as our lucky winner this month. "
        "To claim your £500 Amazon gift card, simply reply with your full name, "
        "home address and date of birth. This offer is valid for 48 hours only."
    ),
    "📅 Benign Message (Low Risk)": (
        "Hi, just a reminder that your dentist appointment is tomorrow at 10am. "
        "Please call us on 01234 567890 if you need to reschedule. See you then!"
    ),
}


def render() -> None:
    """Render the full Analyze page."""
    st.header("🔍 Scam Analyzer")
    st.markdown(
        "Paste a suspicious message below — an SMS, email, job offer, delivery notice, "
        "or anything that doesn't feel right. We'll break down what looks suspicious and why."
    )

    render_disclaimer()

    # Demo message selector
    demo_choice = st.selectbox(
        "Or load a demo message:",
        options=list(DEMO_MESSAGES.keys()),
        key="analyze_demo_select",
    )

    default_text = DEMO_MESSAGES.get(demo_choice, "")

    message_text = st.text_area(
        "Paste your message here:",
        value=default_text,
        height=160,
        max_chars=2000,
        placeholder="e.g. 'Your parcel could not be delivered. Pay £2.99 at fake-link.com'",
        key="analyze_message_input",
    )

    char_count = len(message_text)
    if char_count > 0:
        color = "#c0392b" if char_count > 1900 else "#7f8c8d"
        st.markdown(
            f'<p style="font-size:0.8rem; color:{color}; text-align:right;">'
            f"{char_count} / 2000 characters</p>",
            unsafe_allow_html=True,
        )

    col_btn, col_clear = st.columns([3, 1])
    with col_btn:
        analyze_clicked = st.button(
            "🔎 Analyze Message",
            type="primary",
            use_container_width=True,
            disabled=char_count == 0,
        )
    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.session_state["analyze_result"] = None
            st.session_state["analyze_message_input"] = ""
            st.rerun()

    # Run analysis when button is clicked
    if analyze_clicked:
        if not message_text.strip():
            st.warning("Please paste a message before clicking Analyze.")
        else:
            with st.spinner("Analyzing message…"):
                service = _get_analysis_service()
                result, error = service.run(message_text)

            if error:
                st.warning(f"⚠️ {error}")
                st.session_state["analyze_result"] = None
                st.session_state["analyze_input_text"] = message_text
            else:
                st.session_state["analyze_result"] = result
                st.session_state["analyze_input_text"] = message_text

    # Render cached result (persists across widget interactions)
    result = st.session_state.get("analyze_result")
    input_text = st.session_state.get("analyze_input_text", "")

    if result is not None:
        _render_result(result, input_text)


def _render_result(result, input_text: str) -> None:
    """Render the full analysis result below the input form."""
    st.divider()
    st.subheader("📋 Analysis Result")

    if result.is_fallback:
        render_fallback_notice()

    render_risk_badge(result.risk_level)
    render_risk_summary(result.risk_summary)

    # Highlighted message
    if not result.is_fallback and input_text:
        st.markdown("#### Your message — suspicious phrases highlighted:")
        all_quotes = [q for tactic in result.tactics for q in tactic.evidence_quotes]
        render_highlighted_message(input_text, all_quotes)

    # Detected tactics
    if not result.is_fallback:
        st.markdown("#### ⚠️ Warning Signs Detected")
        render_tactic_cards(result.tactics)

    # Recommended actions
    st.markdown("#### ✅ What You Should Do")
    render_actions(result.recommended_actions)

    # Educational takeaway
    if result.learn_tactic_id:
        st.markdown("#### 📚 Learn About This Tactic")
        render_learn_card(result.learn_tactic_id)

    # Footer disclaimer
    st.divider()
    st.caption(
        "⚠️ This tool provides risk-oriented guidance for educational awareness only. "
        "It does not constitute legal or security advice, and cannot definitively confirm fraud. "
        "When in doubt, contact the organisation directly through their official website."
    )


@st.cache_resource
def _get_analysis_service() -> AnalysisService:
    """Create and cache the AnalysisService (creates one AIAnalyzer per session)."""
    return AnalysisService(AIAnalyzer())
