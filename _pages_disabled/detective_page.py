"""Detective Mode page — INVESTIGATE.

The user inspects a pre-written sample scam message, selects which
phrases look suspicious, submits their selection, and receives a score
with a full explanation of the scam tactics used.

Score-inflation fix (B5): each scenario is counted only once per session.
Retrying a scenario does not increment the challenge count or recalculate
the session average.
"""

import streamlit as st

from services.detective_service import DetectiveService
from ui.components import render_learn_card

_service = DetectiveService()


def render() -> None:
    """Render the Detective Mode page."""
    st.header("🕵️ Detective Mode")
    st.markdown(
        "Think like a scam detective! Read the sample message below and select every phrase "
        "that looks suspicious. Submit your choices to find out how many clues you spotted "
        "— and learn exactly why each one is a warning sign."
    )

    # Session state initialisation (also set in app.py, but defensive here)
    if "detective_score_total" not in st.session_state:
        st.session_state["detective_score_total"] = 0
    if "detective_challenges_done" not in st.session_state:
        st.session_state["detective_challenges_done"] = 0
    # Set of scenario IDs already scored this session (prevents inflation on retry)
    if "detective_scored_ids" not in st.session_state:
        st.session_state["detective_scored_ids"] = set()

    # ------------------------------------------------------------------
    # Scenario selector
    # ------------------------------------------------------------------
    scenarios = _service.get_all_scenarios()
    scenario_titles = {s.scenario_id: s.title for s in scenarios}
    selected_id = st.selectbox(
        "Choose a scenario:",
        options=list(scenario_titles.keys()),
        format_func=lambda sid: scenario_titles[sid],
        key="detective_scenario_select",
    )

    scenario = _service.get_scenario(selected_id)

    # Reset result when scenario changes (but NOT the cumulative score)
    prev_scenario = st.session_state.get("detective_prev_scenario")
    if prev_scenario != selected_id:
        st.session_state["detective_result"] = None
        st.session_state["detective_selections"] = []
        st.session_state["detective_prev_scenario"] = selected_id

    # ------------------------------------------------------------------
    # Show the message
    # ------------------------------------------------------------------
    st.markdown("#### 📩 Read this message carefully:")
    st.markdown(
        f'<div style="'
        f"background-color:#f8f9fa; border:1px solid #dee2e6; border-radius:6px; "
        f'padding:14px; font-size:1rem; line-height:1.7; font-family: monospace;">'
        f"{scenario.message_text}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")

    # ------------------------------------------------------------------
    # Phrase selection
    # ------------------------------------------------------------------
    st.markdown("#### 🔎 Which phrases look suspicious to you?")
    st.caption("Select all that apply, then click Submit.")

    selected_indices: list[int] = []
    for i, phrase in enumerate(scenario.phrases):
        checked = st.checkbox(f'"{phrase}"', key=f"detective_phrase_{selected_id}_{i}")
        if checked:
            selected_indices.append(i)

    col_submit, col_reset = st.columns([3, 1])
    with col_submit:
        submit_clicked = st.button(
            "🔎 Submit My Answers",
            type="primary",
            use_container_width=True,
        )
    with col_reset:
        if st.button("Reset", use_container_width=True):
            st.session_state["detective_result"] = None
            for i in range(len(scenario.phrases)):
                key = f"detective_phrase_{selected_id}_{i}"
                if key in st.session_state:
                    st.session_state[key] = False
            st.rerun()

    if submit_clicked:
        if not selected_indices:
            st.warning("Please select at least one suspicious phrase before submitting.")
        else:
            result = _service.score_attempt(scenario, selected_indices)
            st.session_state["detective_result"] = result

            # B5 fix: only count each scenario once in the session score.
            # Retrying the same scenario does NOT re-increment the totals.
            scored_ids: set = st.session_state["detective_scored_ids"]
            if selected_id not in scored_ids:
                st.session_state["detective_score_total"] += result.score
                st.session_state["detective_challenges_done"] += 1
                scored_ids.add(selected_id)
                st.session_state["detective_scored_ids"] = scored_ids

    # ------------------------------------------------------------------
    # Show result if available
    # ------------------------------------------------------------------
    detective_result = st.session_state.get("detective_result")
    if detective_result is not None:
        _render_result(detective_result, scenario, selected_indices)


def _render_result(result, scenario, selected_indices: list[int]) -> None:
    """Render the scoring result, per-phrase WHY explanations, and tactic context."""
    st.divider()
    st.subheader("📊 Your Result")

    # Score display
    score_color = "#1e8449" if result.score >= 70 else ("#d68910" if result.score >= 40 else "#c0392b")
    st.markdown(
        f'<div style="'
        f"background-color:#f8f9fa; border-radius:8px; padding:16px; "
        f'text-align:center;">'
        f'<span style="font-size:3rem; font-weight:800; color:{score_color};">'
        f"{result.score}</span>"
        f'<span style="font-size:1.5rem; color:{score_color};">/100</span>'
        f"<br/>"
        f'<span style="font-size:1rem; color:#444;">{result.feedback}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Correct clues found", f"{result.correct_count} / {result.total_correct}")
    col2.metric("False alarms", len(result.false_positive_indices))
    col3.metric("Clues missed", len(result.missed_indices))

    # ------------------------------------------------------------------
    # Per-phrase answer key with WHY explanations
    # ------------------------------------------------------------------
    st.markdown("#### 🔑 Answer Key — Why each phrase is or is not suspicious")

    for i, phrase in enumerate(scenario.phrases):
        is_correct = i in scenario.correct_phrase_indices
        was_selected = i in selected_indices

        if is_correct and was_selected:
            st.markdown(
                f'<div style="background:#eafaf1; border-left:4px solid #27ae60; '
                f'padding:8px 14px; margin:4px 0; border-radius:4px;">'
                f'✅ <strong>"{phrase}"</strong> — '
                f"<em>Suspicious — you spotted it!</em>"
                f"</div>",
                unsafe_allow_html=True,
            )
        elif is_correct and not was_selected:
            st.markdown(
                f'<div style="background:#fdf0ef; border-left:4px solid #e74c3c; '
                f'padding:8px 14px; margin:4px 0; border-radius:4px;">'
                f'❌ <strong>"{phrase}"</strong> — '
                f"<em>Suspicious — you missed this one</em>"
                f"</div>",
                unsafe_allow_html=True,
            )
        elif not is_correct and was_selected:
            st.markdown(
                f'<div style="background:#fef9e7; border-left:4px solid #f39c12; '
                f'padding:8px 14px; margin:4px 0; border-radius:4px;">'
                f'⚠️ "{phrase}" — '
                f"<em>Not suspicious (false alarm)</em>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:#f8f9fa; border-left:4px solid #dee2e6; '
                f'padding:8px 14px; margin:4px 0; border-radius:4px;">'
                f'○ "{phrase}" — <em>Not suspicious</em>'
                f"</div>",
                unsafe_allow_html=True,
            )

    # ------------------------------------------------------------------
    # Detailed manipulation explanation — teaches the WHY
    # ------------------------------------------------------------------
    st.markdown("#### 💡 How This Scam Works — The Manipulation Behind It")
    st.markdown(scenario.explanation)

    # ------------------------------------------------------------------
    # Learn card linked to the scenario's primary tactic
    # ------------------------------------------------------------------
    if scenario.tactic_id:
        st.markdown("#### 📚 Deep Dive: Learn About This Tactic")
        render_learn_card(scenario.tactic_id)

    # ------------------------------------------------------------------
    # Running session score (only shown after at least one scenario scored)
    # ------------------------------------------------------------------
    done = st.session_state.get("detective_challenges_done", 0)
    total = st.session_state.get("detective_score_total", 0)
    scored_ids: set = st.session_state.get("detective_scored_ids", set())

    if done > 0:
        average = round(total / done)
        already_scored = selected_id in scored_ids
        retry_note = " (retried — score not recounted)" if already_scored else ""
        st.divider()
        st.caption(
            f"🏅 Session progress: {done} unique scenario(s) completed — "
            f"average score {average}/100{retry_note}"
        )
