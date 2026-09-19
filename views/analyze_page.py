"""Analyze page — DETECT + EXPLAIN.

The user pastes a suspicious message here, submits it for analysis,
and receives a structured risk assessment with highlighted evidence,
tactic explanations, safe actions, and an educational takeaway.
"""

import os

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
        <div class="hero-panel">
            <div class="eyebrow">Your personal cyber safety guide</div>
            <h1 style="margin:6px 0; font-size:2rem;">🛡️ Check a message before you trust it</h1>
            <p style="margin:0; font-size:1rem;">
                Paste an SMS, WhatsApp, email, or job offer. We explain the warning signs in plain language
                and suggest the safest next step.
            </p>
            <div class="hero-meta">● SCAN MODE READY &nbsp;&nbsp; • &nbsp;&nbsp; PRIVATE BY DESIGN &nbsp;&nbsp; • &nbsp;&nbsp; BEGINNER FRIENDLY</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Your 3-step safety check")
    step_one, step_two, step_three = st.columns(3)
    for column, number, title, text in (
        (step_one, "01", "Paste safely", "Remove passwords, PINs, OTPs, and card details first."),
        (step_two, "02", "Run a check", "Use a demo or paste a message, then select Analyze."),
        (step_three, "03", "Act safely", "Review the evidence and use official channels to verify."),
    ):
        with column:
            st.markdown(
                f'<div class="step-card"><div class="step-number">{number}</div>'
                f"<h3>{title}</h3><p>{text}</p></div>", unsafe_allow_html=True
            )

    st.markdown("### 🔍 Analyze a Message")

    render_disclaimer()

    st.info("New here? Choose a demo below first. It is the fastest way to see how the checker works.", icon="👋")

    # ------------------------------------------------------------------
    # Demo selector — changing demo clears any previous result (B2 fix)
    # ------------------------------------------------------------------
    demo_choice = st.selectbox(
        "Load a demo message to try:",
        options=list(DEMO_MESSAGES.keys()),
        key="analyze_demo_select",
    )

    # Load the selected demo into the actual text-area widget.  Supplying only
    # ``value=`` does not update a keyed Streamlit widget after its first render.
    # That made demo selections appear to do nothing and could leave stale results.
    prev_demo = st.session_state.get("analyze_prev_demo")
    if prev_demo != demo_choice:
        st.session_state["analyze_result"] = None
        st.session_state["analyze_input_text"] = DEMO_MESSAGES.get(demo_choice, "")
        st.session_state["analyze_message_input"] = DEMO_MESSAGES.get(demo_choice, "")
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
    else:
        st.markdown("#### What this checker looks for")
        feature_one, feature_two, feature_three = st.columns(3)
        feature_one.markdown("**⏰ Pressure**\n\nDeadlines, threats, or ‘act now’ language.")
        feature_two.markdown("**🔗 Unsafe links**\n\nUnexpected websites or requests to click.")
        feature_three.markdown("**🔐 Data requests**\n\nAsking for OTPs, banking information, or money.")


def _render_result(result, input_text: str) -> None:
    """Render the full analysis result below the input form."""
    st.divider()
    st.subheader("📋 Analysis Result")

    if result.is_fallback:
        render_fallback_notice()
        _render_dev_diagnostic(result)

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


def _render_dev_diagnostic(result) -> None:
    """Show a collapsible developer diagnostic panel when analysis falls back.

    Displays sanitized error information — never reveals API keys or secrets.
    Intended for developers/hackathon judges to understand why AI failed.
    Hidden inside an expander so it does not disrupt the normal user experience.
    """
    reason = getattr(result, "fallback_reason", "") or "unknown"
    debug_msg = getattr(result, "fallback_debug", "") or ""

    # Friendly labels for each error category
    reason_labels: dict[str, tuple[str, str]] = {
        "no_api_key":      ("🔑 No API Key",        "GEMINI_API_KEY is missing or set to the placeholder value in .env"),
        "transient":       ("🔄 Temporary Unavailable", "Gemini returned a 503/502 error. All retries exhausted. Try again shortly."),
        "model_not_found": ("📛 Model Not Found",    "The Gemini model name in the code is no longer available or was renamed."),
        "auth_error":      ("🚫 Authentication Error", "The API key was rejected (invalid, expired, or wrong key type)."),
        "quota_exceeded":  ("⏱️ Quota Exceeded",     "The API rate limit or daily quota has been reached."),
        "api_error":       ("⚠️ Gemini API Error",   "The Gemini API returned an unexpected HTTP error."),
        "parse_fail":      ("🔍 Response Parse Error", "The AI response was received but could not be parsed as JSON."),
        "network_error":   ("🌐 Network Error",      "Could not reach the Gemini API (connection, DNS, or timeout)."),
        "unexpected":      ("❓ Unexpected Error",   "An unexpected error occurred during AI analysis."),
    }
    label, hint = reason_labels.get(reason, ("❓ Unknown Error", "An unknown error occurred."))

    # Key status (present/absent/placeholder) — length only, never the value
    api_key = os.getenv("GEMINI_API_KEY", "")
    placeholder = "your_gemini_api_key_here"
    if not api_key:
        key_status = "❌ Not present (GEMINI_API_KEY missing from environment)"
    elif api_key == placeholder:
        key_status = "❌ Placeholder value (replace with a real key in .env)"
    else:
        key_status = f"✅ Present (length: {len(api_key)} characters)"

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    with st.expander("🛠️ Developer Diagnostic — click to expand", expanded=False):
        st.markdown(f"**Error category:** {label}")
        st.markdown(f"**Hint:** {hint}")
        st.markdown(f"**API key status:** {key_status}")
        st.markdown(f"**Model:** `{model_name}`")
        if debug_msg:
            st.markdown("**Sanitized error message:**")
            st.code(debug_msg, language=None)
        st.caption(
            "This panel is for debugging only. API key values are never shown here. "
            "Remove or disable this panel before deploying to production."
        )


@st.cache_resource
def _get_analysis_service() -> AnalysisService:
    """Create and cache the AnalysisService (creates one AIAnalyzer per app run)."""
    return AnalysisService(AIAnalyzer())


# Streamlit treats files inside a ``pages`` directory as direct routes.  Keep
# this route useful when opened at /analyze_page instead of leaving a blank page.
if __name__ == "__main__":
    st.set_page_config(page_title="Analyze a Message | AI Scam Detective", page_icon="🛡️", layout="centered")
    from ui.theme import apply_theme

    apply_theme()
    render()
