"""Detective Mode page — INVESTIGATE.

The user inspects a pre-written sample scam message, selects which
phrases look suspicious, submits their selection, and receives a score
with a full explanation of the scam tactics used.
"""

import streamlit as st

from data.tactics_library import TACTICS_LIBRARY
from services.detective_service import DetectiveService
from ui.components import render_learn_card

_service = DetectiveService()


def render() -> None:
    """Render the Detective Mode page."""
    st.header("🕵️ Detective Mode")
    st.markdown(
        "Think like a scam detective! Read the sample message below and select every phrase "
        "that looks suspicious. Submit your choices to find out how many clues you spotted."
    )

    # Session state initialisation
    if "detective_score_total" not in st.session_state:
        st.session_state["detective_score_total"] = 0
    if "detective_challenges_done" not in st.session_state:
        st.session_state["detective_challenges_done"] = 0

    # Scenario selector
    scenarios = _service.get_all_scenarios()
    scenario_titles = {s.scenario_id: s.title for s in scenarios}
    selected_id = st.selectbox(
        "Choose a scenario:",
        options=list(scenario_titles.keys()),
        format_func=lambda sid: scenario_titles[sid],
        key="detective_scenario_select",
    )

    scenario = _service.get_scenario(selected_id)

    # Reset result when scenario changes
    prev_scenario = st.session_state.get("detective_prev_scenario")
    if prev_scenario != selected_id:
        st.session_state["detective_result"] = None
        st.session_state["detective_selections"] = []
        st.session_state["detective_prev_scenario"] = selected_id

    # Show the message
    st.markdown("#### 📩 Read this message carefully:")
    st.markdown(
        f'<div style="'
        f"background-color:#f8f9fa; border:1px solid #dee2e6; border-radius:6px; "
        f'padding:14px; font-size:1rem; line-height:1.7; font-family: monospace;">'
        f"{scenario.message_text}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")

    # Phrase selection
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
            # Clear all phrase checkboxes for this scenario
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
            # Update running score
            st.session_state["detective_score_total"] += result.score
            st.session_state["detective_challenges_done"] += 1

    # Show result if available
    detective_result = st.session_state.get("detective_result")
    if detective_result is not None:
        _render_result(detective_result, scenario, selected_indices)


def _render_result(result, scenario, selected_indices: list[int]) -> None:
    """Render the scoring result and explanation."""
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

    # Breakdown table
    col1, col2, col3 = st.columns(3)
    col1.metric("Correct clues found", f"{result.correct_count} / {result.total_correct}")
    col2.metric("False alarms", len(result.false_positive_indices))
    col3.metric("Clues missed", len(result.missed_indices))

    # Show what was correct / missed
    st.markdown("#### 🔑 Answer Key")

    for i, phrase in enumerate(scenario.phrases):
        is_correct = i in scenario.correct_phrase_indices
        was_selected = i in selected_indices

        if is_correct and was_selected:
            st.markdown(f'✅ **"{phrase}"** — Suspicious (you spotted it!)')
        elif is_correct and not was_selected:
            st.markdown(f'❌ **"{phrase}"** — Suspicious (you missed this one)')
        elif not is_correct and was_selected:
            st.markdown(f'⚠️ "{phrase}" — Not suspicious (this was a false alarm)')
        else:
            st.markdown(f'○ "{phrase}" — Not suspicious')

    # Detailed explanation
    st.markdown("#### 💡 Explanation")
    st.markdown(scenario.explanation)

    # Link to Learn section
    if scenario.tactic_id:
        st.markdown("#### 📚 Learn More About This Tactic")
        render_learn_card(scenario.tactic_id)

    # Running score in session
    total = st.session_state.get("detective_score_total", 0)
    done = st.session_state.get("detective_challenges_done", 0)
    if done > 0:
        average = round(total / done)
        st.divider()
        st.caption(
            f"🏅 Session progress: {done} challenge(s) completed — "
            f"average score {average}/100"
        )
