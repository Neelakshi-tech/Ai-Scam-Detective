"""Shared Streamlit rendering functions for AI Scam Detective.

All functions in this module are pure presentational helpers.
They accept data objects and render Streamlit UI — no business logic.
"""

import html
import re

import streamlit as st

from data.models import AnalysisResult, Tactic
from data.tactics_library import TACTICS_LIBRARY

# ---------------------------------------------------------------------------
# Risk level configuration
# ---------------------------------------------------------------------------

_RISK_CONFIG = {
    "High": {
        "icon": "🔴",
        "label": "High Risk",
        "color": "#c0392b",
        "bg": "#fdf0ef",
        "border": "#e74c3c",
        "message": "Multiple warning signs detected. Treat this message with great caution.",
    },
    "Medium": {
        "icon": "🟡",
        "label": "Medium Risk",
        "color": "#d68910",
        "bg": "#fef9e7",
        "border": "#f39c12",
        "message": "Some warning signs detected. Verify before taking any action.",
    },
    "Low": {
        "icon": "🟢",
        "label": "Low Risk",
        "color": "#1e8449",
        "bg": "#eafaf1",
        "border": "#27ae60",
        "message": "No significant warning signs detected — but always stay cautious.",
    },
    "Unknown": {
        "icon": "⚪",
        "label": "Analysis Unavailable",
        "color": "#7f8c8d",
        "bg": "#f2f3f4",
        "border": "#bdc3c7",
        "message": "AI analysis was unavailable. See the safe actions below.",
    },
}


# ---------------------------------------------------------------------------
# Public rendering functions
# ---------------------------------------------------------------------------


def render_disclaimer() -> None:
    """Render the privacy and safety disclaimer banner."""
    st.warning(
        "⚠️ **Privacy reminder:** Do not paste real passwords, PINs, OTPs, "
        "banking credentials, or card numbers. "
        "This tool is for **educational awareness only** and does not store your messages.",
        icon=None,
    )


def render_risk_badge(risk_level: str) -> None:
    """Render a colored risk-level badge with icon and label.

    Args:
        risk_level: One of 'Low', 'Medium', 'High', or 'Unknown'.
    """
    cfg = _RISK_CONFIG.get(risk_level, _RISK_CONFIG["Unknown"])
    # All values are internal constants — safe to interpolate directly.
    st.markdown(
        f"""
        <div style="
            background-color: {cfg['bg']};
            border: 2px solid {cfg['border']};
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 8px;
        ">
            <span style="font-size: 2rem;">{cfg['icon']}</span>
            <span style="
                font-size: 1.4rem;
                font-weight: 700;
                color: {cfg['color']};
                margin-left: 10px;
            ">{cfg['label']}</span>
            <p style="margin: 8px 0 0 0; color: #444; font-size: 0.95rem;">
                {cfg['message']}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_uncertainty_note(tactic_count: int, is_fallback: bool) -> None:
    """Render a short AI-uncertainty note below the risk badge.

    This communicates clearly that risk assessment is based on pattern
    recognition and is not proof of fraud. This is always shown.

    Args:
        tactic_count: Number of tactics detected (0 = no signals found).
        is_fallback:  True when AI analysis was unavailable.
    """
    if is_fallback:
        return  # Fallback notice is shown separately

    if tactic_count == 0:
        note = (
            "No warning patterns were detected in this message. "
            "This does not guarantee the message is safe — always use your judgment "
            "and verify through official channels if you are uncertain."
        )
    elif tactic_count == 1:
        note = (
            f"**{tactic_count} warning pattern** was identified by AI analysis. "
            "This is based on language patterns, not verified facts. "
            "Independently verify any unexpected request before taking action."
        )
    else:
        note = (
            f"**{tactic_count} warning patterns** were identified by AI analysis. "
            "This is based on language patterns, not verified facts. "
            "Independently verify any unexpected request before taking action."
        )

    st.caption(f"ℹ️ {note}")


def render_risk_summary(summary: str) -> None:
    """Render the AI's plain-English risk summary sentence.

    Args:
        summary: One or two sentences describing the overall risk.
    """
    if summary:
        st.markdown(f"**{summary}**")


def render_highlighted_message(text: str, all_quotes: list[str]) -> None:
    """Render the original message with suspicious phrases highlighted.

    Uses HTML <mark> tags via unsafe_allow_html. Only quotes that
    literally appear in the text are highlighted (validation is already
    done upstream by AnalysisService._filter_evidence_quotes, but this
    function also checks defensively).

    The replacement uses a lambda to avoid regex backreference injection
    (B4 fix): if a quote string contains backslash sequences like \\1,
    passing it as a replacement string to re.sub would be misinterpreted.
    Using a lambda makes the replacement literal.

    Args:
        text:       The original (sanitized) message text.
        all_quotes: Flat list of evidence quote strings to highlight.
    """
    if not all_quotes:
        # No highlights — render in a plain pre-formatted box
        st.markdown(
            f'<div style="background-color:#f8f9fa; border:1px solid #dee2e6; '
            f'border-radius:6px; padding:14px; font-size:0.95rem; line-height:1.6; '
            f'white-space:pre-wrap;">{html.escape(text)}</div>',
            unsafe_allow_html=True,
        )
        return

    # HTML-escape the full message first so user input cannot inject tags.
    highlighted = html.escape(text)

    # Sort by length descending to avoid partial replacements of shorter
    # quotes that are substrings of longer ones.
    sorted_quotes = sorted(set(all_quotes), key=len, reverse=True)

    for quote in sorted_quotes:
        if not quote:
            continue
        escaped_quote = html.escape(quote)
        if escaped_quote not in highlighted:
            continue
        pattern = re.escape(escaped_quote)
        mark_open = '<mark style="background-color:#fff176; padding:1px 2px; border-radius:3px;">'
        mark_close = "</mark>"
        # Use a lambda so the replacement is treated as a literal string,
        # not as a regex replacement pattern (fixes B4 backreference bug).
        highlighted = re.sub(
            pattern,
            lambda m, o=mark_open, c=mark_close, q=escaped_quote: f"{o}{q}{c}",
            highlighted,
        )

    st.markdown(
        f'<div style="background-color:#f8f9fa; border:2px solid #f39c12; '
        f'border-radius:6px; padding:14px; font-size:0.95rem; line-height:1.7; '
        f'white-space:pre-wrap;">'
        f"{highlighted}</div>",
        unsafe_allow_html=True,
    )


def render_tactic_cards(tactics: list[Tactic]) -> None:
    """Render one expandable card per detected tactic.

    Cards are collapsed by default so the page does not become
    overwhelming when many tactics are detected (U1 fix).

    Args:
        tactics: List of Tactic objects from the AnalysisResult.
    """
    if not tactics:
        st.info("No specific scam tactics were identified in this message.", icon="ℹ️")
        return

    for tactic in tactics:
        icon = TACTICS_LIBRARY.get(tactic.tactic_id, {}).get("icon", "⚠️")
        with st.expander(f"{icon} {tactic.tactic_name}", expanded=False):
            st.markdown(tactic.explanation)

            if tactic.evidence_quotes:
                st.markdown("**Warning signs found in your message:**")
                for quote in tactic.evidence_quotes:
                    # Escape user-derived / AI-returned content before rendering HTML.
                    safe_quote = html.escape(quote)
                    st.markdown(
                        f'<blockquote style="'
                        f"border-left:4px solid #e74c3c; margin:4px 0; "
                        f'padding:6px 12px; color:#555; font-style:italic;">'
                        f'"{safe_quote}"</blockquote>',
                        unsafe_allow_html=True,
                    )


def render_actions(actions: list[str]) -> None:
    """Render a list of safe recommended actions.

    Args:
        actions: List of plain-English action strings.
    """
    if not actions:
        return
    for action in actions:
        st.markdown(f"✅ {action}")


def render_india_reporting() -> None:
    """Render the India-specific cybercrime reporting guidance block.

    Only shown for Medium and High risk results. Links are to official
    Indian government cybercrime resources. No government affiliation
    or endorsement is claimed.
    """
    st.markdown(
        """
        <div style="
            background-color: #fff8e1;
            border: 1px solid #ffe082;
            border-radius: 8px;
            padding: 14px 18px;
            font-size: 0.92rem;
        ">
            <strong>🇮🇳 Reporting in India</strong><br/>
            If you believe this is a scam, you can report it through official channels:
            <ul style="margin: 8px 0 0 0; padding-left: 18px;">
                <li>
                    <strong>National Cyber Crime Reporting Portal:</strong>
                    <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">
                        cybercrime.gov.in
                    </a>
                </li>
                <li>
                    <strong>Cyber Crime Helpline:</strong> Dial <strong>1930</strong>
                    (Ministry of Home Affairs, India)
                </li>
                <li>
                    <strong>Spam SMS / calls:</strong> Forward details to
                    <strong>1909</strong> (TRAI DND registry)
                </li>
            </ul>
            <span style="font-size:0.82rem; color:#888;">
                This tool is not affiliated with or endorsed by any government body.
                These are publicly available official reporting resources.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_learn_card(tactic_id: str) -> None:
    """Look up and render the educational card for a tactic.

    Args:
        tactic_id: The ID of the tactic to display (e.g. 'URGENCY').
    """
    if not tactic_id:
        return
    tactic = TACTICS_LIBRARY.get(tactic_id)
    if not tactic:
        return

    icon = tactic.get("icon", "📚")
    # All content here is from the static TACTICS_LIBRARY — safe to render directly.
    # User input is never passed into this function.
    st.markdown(
        f"""
        <div style="
            background-color: #eef2ff;
            border: 1px solid #c7d2fe;
            border-radius: 8px;
            padding: 16px 20px;
        ">
            <h4 style="margin:0 0 8px 0; color:#3730a3;">
                {icon} Learn: {tactic['name']}
            </h4>
            <p style="margin:0 0 8px 0;">{tactic['description']}</p>
            <p style="margin:0 0 4px 0;"><strong>Example:</strong> {tactic['example']}</p>
            <p style="margin:0 0 4px 0;"><strong>What to watch for:</strong> {tactic['warning']}</p>
            <p style="
                margin:8px 0 0 0;
                background-color:#dbeafe;
                border-radius:4px;
                padding:8px 12px;
                font-size:0.9rem;
            ">💡 <strong>Safe tip:</strong> {tactic['tip']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_fallback_notice() -> None:
    """Render a notice explaining that AI analysis was unavailable."""
    st.info(
        "**AI analysis is currently unavailable.** "
        "This may be because no API key is configured or the service is temporarily unreachable. "
        "The safe actions below are general guidance you can always follow.",
        icon="ℹ️",
    )
