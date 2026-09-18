"""Shared Streamlit rendering functions for AI Scam Detective.

All functions in this module are pure presentational helpers.
They accept data objects and render Streamlit UI — no business logic.
"""

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
    literally appear in the text are highlighted.

    Args:
        text:       The original (sanitized) message text.
        all_quotes: Flat list of evidence quote strings to highlight.
    """
    if not all_quotes:
        st.markdown(f"```\n{text}\n```")
        return

    highlighted = text
    # Sort by length descending to avoid partial replacements of shorter quotes
    # that are substrings of longer ones.
    sorted_quotes = sorted(all_quotes, key=len, reverse=True)

    for quote in sorted_quotes:
        if quote and quote in highlighted:
            escaped = re.escape(quote)
            highlighted = re.sub(
                escaped,
                f'<mark style="background-color:#fff176; padding:1px 2px; border-radius:3px;">'
                f"{quote}</mark>",
                highlighted,
            )

    st.markdown(
        f'<div style="'
        f"background-color:#f8f9fa; border:1px solid #dee2e6; border-radius:6px; "
        f'padding:14px; font-size:0.95rem; line-height:1.6;">'
        f"{highlighted}</div>",
        unsafe_allow_html=True,
    )


def render_tactic_cards(tactics: list[Tactic]) -> None:
    """Render one expandable card per detected tactic.

    Args:
        tactics: List of Tactic objects from the AnalysisResult.
    """
    if not tactics:
        st.info("No specific scam tactics were identified in this message.", icon="ℹ️")
        return

    for tactic in tactics:
        icon = TACTICS_LIBRARY.get(tactic.tactic_id, {}).get("icon", "⚠️")
        with st.expander(f"{icon} {tactic.tactic_name}", expanded=True):
            st.markdown(tactic.explanation)

            if tactic.evidence_quotes:
                st.markdown("**Warning signs found in your message:**")
                for quote in tactic.evidence_quotes:
                    st.markdown(
                        f'<blockquote style="'
                        f"border-left:4px solid #e74c3c; margin:4px 0; "
                        f'padding:6px 12px; color:#555; font-style:italic;">'
                        f'"{quote}"</blockquote>',
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
