"""Analyze page — DETECT + EXPLAIN.

The user pastes a suspicious message here, submits it for analysis,
and receives a structured risk assessment with highlighted evidence,
tactic explanations, safe actions, and an educational takeaway.
"""

import streamlit as st

from ai.ai_analyzer import AIAnalyzer
from services.analysis_service import AnalysisService
from ui.components import (
    render_actions,
    render_disclaimer,
    render_fallback_notice,
    render_highlighted_message,
    render_india_reporting,
    render_learn_card,
    render_risk_badge,
    render_risk_summary,
    render_tactic_cards,
    render_uncertainty_note,
)

# ---------------------------------------------------------------------------
# India-context demo messages (fictional details, educational purpose only)
# ---------------------------------------------------------------------------

DEMO_MESSAGES: dict[str, str] = {
    "Select a demo…": "",
    "📦 Fake Delivery / Refund (UPI)": (
        "Dear Customer, your Meesho order #MS4921 has been returned by courier. "
        "To initiate your refund of ₹899, click: meesho-refund-secure.net "
        "Enter your UPI ID and the OTP you receive. "
        "Refund expires in 24 hours if not claimed. "
        "Ignore this and we will cancel your account."
    ),
    "🏦 Fake KYC / Bank SMS": (
        "ALERT: Your SBI account has been suspended due to incomplete KYC. "
        "To restore access, verify now at: sbi-kyc-verify.info "
        "You will need your account number, ATM PIN, and Aadhaar OTP. "
        "Non-compliance within 6 hours will result in permanent account closure. "
        "This is a mandatory directive. — SBI Customer Care"
    ),
    "💼 Fake Work-from-Home Job": (
        "Hello! We came across your profile on LinkedIn. "
        "We are hiring for a remote data-entry position paying ₹45,000/month. "
        "No qualifications required. Training provided. "
        "To register, pay ₹599 via Google Pay and send a screenshot to this number. "
        "Also share your bank IFSC and account number for salary processing. "
        "Offer valid only until midnight tonight. Only 5 openings left!"
    ),
    "🏛️ Fake Income Tax Refund": (
        "NOTICE: Income Tax Department — A refund of ₹12,340 is pending for PAN CXXXS9876G. "
        "Claim at: incometax-refundportal.com within 48 hours to avoid cancellation. "
        "Enter your bank account details, IFSC, and Aadhaar number to proceed. "
        "Failure to respond will result in a scrutiny notice."
    ),
    "🎁 Fake Prize / Lucky Draw": (
        "Congratulations! You have been selected as the winner of KBC Season 16. "
        "Your prize amount is ₹25 Lakh. "
        "To claim, call 09876543210 and pay a processing fee of ₹2,500 via PhonePe. "
        "Share your full name, date of birth, and Aadhaar number to verify your identity. "
        "Offer valid for 48 hours only. Limited slots available!"
    ),
    "📅 Normal Message (Low Risk)": (
        "Hi, your HDFC Bank statement for the month of May is ready. "
        "You can view it by logging into your NetBanking account at hdfcbank.com. "
        "If you need help, call our official customer care at 1800-202-6161. "
        "Do not share your OTP or password with anyone."
    ),
}


def render() -> None:
    """Render the full Analyze page."""
    # ------------------------------------------------------------------
    # Product hero
    # ------------------------------------------------------------------
    st.markdown(
        """
        <div style="padding: 8px 0 18px 0;">
            <h1 style="margin:0; font-size:1.9rem;">🕵️ AI Scam Detective</h1>
            <p style="margin:4px 0 0 0; color:#555; font-size:1rem;">
                Paste any suspicious message — SMS, WhatsApp, email, or job offer —
                and we'll break down <strong>exactly what looks suspicious and why</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.header("🔍 Analyze a Message")

    render_disclaimer()

    # ------------------------------------------------------------------
    # Demo selector — changing demo clears any previous result (B2 fix)
    # ------------------------------------------------------------------
    demo_choice = st.selectbox(
        "Load a demo message to try:",
        options=list(DEMO_MESSAGES.keys()),
        key="analyze_demo_select",
    )

    # Clear stale result when the user switches to a different demo
    prev_demo = st.session_state.get("analyze_prev_demo")
    if prev_demo != demo_choice:
        st.session_state["analyze_result"] = None
        st.session_state["analyze_input_text"] = ""
        st.session_state["analyze_prev_demo"] = demo_choice

    default_text = DEMO_MESSAGES.get(demo_choice, "")

    message_text = st.text_area(
        "Paste your message here:",
        value=default_text,
        height=160,
        max_chars=2000,
        placeholder=(
            "e.g. 'Your KYC is incomplete. Click here to update: fake-bank-link.in. "
            "Your account will be blocked in 24 hours.'"
        ),
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
            st.session_state["analyze_input_text"] = ""
            st.session_state["analyze_prev_demo"] = None
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

    # ------------------------------------------------------------------
    # Risk badge + uncertainty note
    # ------------------------------------------------------------------
    render_risk_badge(result.risk_level)
    render_risk_summary(result.risk_summary)
    render_uncertainty_note(len(result.tactics), result.is_fallback)

    # ------------------------------------------------------------------
    # Highlighted message — shown FIRST as the investigation centrepiece
    # ------------------------------------------------------------------
    if not result.is_fallback and input_text:
        tactic_count = len(result.tactics)
        if tactic_count > 0:
            label = (
                f"#### 🔍 Your message — "
                f"**{tactic_count} warning sign{'s' if tactic_count != 1 else ''} highlighted**"
            )
        else:
            label = "#### 🔍 Your message — no warning signs highlighted"
        st.markdown(label)
        all_quotes = [q for tactic in result.tactics for q in tactic.evidence_quotes]
        render_highlighted_message(input_text, all_quotes)

    # ------------------------------------------------------------------
    # Detected tactics (collapsed by default)
    # ------------------------------------------------------------------
    if not result.is_fallback:
        tactic_count = len(result.tactics)
        if tactic_count > 0:
            st.markdown(f"#### ⚠️ {tactic_count} Warning Sign{'s' if tactic_count != 1 else ''} Detected")
        else:
            st.markdown("#### ⚠️ Warning Signs")
        render_tactic_cards(result.tactics)

    # ------------------------------------------------------------------
    # What should I do?
    # ------------------------------------------------------------------
    st.markdown("#### ✅ What Should I Do?")
    render_actions(result.recommended_actions)

    # India reporting block — shown for Medium and High risk only
    if result.risk_level in ("Medium", "High"):
        st.markdown("")
        render_india_reporting()

    # ------------------------------------------------------------------
    # Educational takeaway
    # ------------------------------------------------------------------
    if result.learn_tactic_id:
        st.markdown("#### 📚 Learn About This Tactic")
        render_learn_card(result.learn_tactic_id)

    # Footer disclaimer
    st.divider()
    st.caption(
        "⚠️ This tool provides risk-oriented guidance for educational awareness only. "
        "It does not constitute legal or security advice, and cannot definitively confirm fraud. "
        "When in doubt, contact the organisation directly through their official website or app."
    )


@st.cache_resource
def _get_analysis_service() -> AnalysisService:
    """Create and cache the AnalysisService (creates one AIAnalyzer per app run)."""
    return AnalysisService(AIAnalyzer())
