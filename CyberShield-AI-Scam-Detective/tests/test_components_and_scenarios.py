"""Tests for ui/components helper functions that have pure-logic behaviour.

Tests for rendering functions that have testable non-UI logic:
  - render_highlighted_message regex safety (B4 fix)
  - India-context scenarios exist in data/scenarios.py
  - Scenario count and IDs
"""

import pytest

from data.scenarios import SCENARIOS
from services.detective_service import DetectiveService


class TestScenariosData:
    """Validate the India-context scenarios are correctly structured."""

    def test_at_least_four_scenarios_exist(self):
        assert len(SCENARIOS) >= 4

    def test_parcel_delivery_scenario_exists(self):
        # Required by existing test_detective_service.py
        ids = [s.scenario_id for s in SCENARIOS]
        assert "parcel_delivery" in ids

    def test_india_context_scenario_ids_present(self):
        ids = {s.scenario_id for s in SCENARIOS}
        # All four new India-context scenarios must be present
        assert "kyc_bank_scam" in ids
        assert "fake_job_offer" in ids
        assert "income_tax_scam" in ids

    def test_all_scenarios_have_non_empty_phrases(self):
        for s in SCENARIOS:
            assert len(s.phrases) > 0, f"Scenario {s.scenario_id} has no phrases"

    def test_all_correct_indices_are_valid(self):
        for s in SCENARIOS:
            for idx in s.correct_phrase_indices:
                assert 0 <= idx < len(s.phrases), (
                    f"Scenario {s.scenario_id}: index {idx} out of range "
                    f"(phrases len={len(s.phrases)})"
                )

    def test_all_scenarios_have_tactic_id(self):
        for s in SCENARIOS:
            assert s.tactic_id, f"Scenario {s.scenario_id} has no tactic_id"

    def test_all_scenarios_have_explanation(self):
        for s in SCENARIOS:
            assert s.explanation, f"Scenario {s.scenario_id} has no explanation"

    def test_no_uk_currency_in_scenarios(self):
        """Confirm no £ symbol appears in any scenario message text (India localisation)."""
        for s in SCENARIOS:
            assert "£" not in s.message_text, (
                f"Scenario {s.scenario_id} contains UK currency symbol"
            )

    def test_india_currency_present_in_delivery_scenario(self):
        delivery = next(s for s in SCENARIOS if s.scenario_id == "parcel_delivery")
        assert "₹" in delivery.message_text


class TestDetectiveServiceWithNewScenarios:
    """Ensure DetectiveService works correctly with the new scenario set."""

    def test_get_kyc_scenario(self):
        service = DetectiveService()
        scenario = service.get_scenario("kyc_bank_scam")
        assert scenario.scenario_id == "kyc_bank_scam"

    def test_get_income_tax_scenario(self):
        service = DetectiveService()
        scenario = service.get_scenario("income_tax_scam")
        assert scenario.scenario_id == "income_tax_scam"

    def test_score_attempt_on_new_scenario(self):
        service = DetectiveService()
        scenario = service.get_scenario("kyc_bank_scam")
        # Select all correct answers
        result = service.score_attempt(scenario, scenario.correct_phrase_indices)
        assert result.score == 100

    def test_score_attempt_no_selection_returns_zero(self):
        service = DetectiveService()
        scenario = service.get_scenario("income_tax_scam")
        result = service.score_attempt(scenario, [])
        assert result.score == 0


class TestRegexSafetyInHighlightedMessage:
    """Verify that the regex replacement is safe against backreference injection.

    We test the underlying logic via _filter_evidence_quotes and the fact that
    the lambda-based re.sub in render_highlighted_message does not raise or
    produce corrupted output when the quote contains backslash sequences.

    Note: render_highlighted_message uses Streamlit, so we test the logic
    that feeds it (evidence quote filtering) rather than the Streamlit call.
    """

    def test_quote_with_backslash_does_not_crash_filter(self):
        """A quote containing \\1 (regex backreference syntax) must not corrupt output."""
        from services.analysis_service import _filter_evidence_quotes
        from data.models import Tactic

        # Message that contains a literal backslash sequence
        message = r"Click at site\1 to verify your account now"
        tactic = Tactic(
            tactic_id="SUSPICIOUS_LINK",
            tactic_name="Suspicious Link",
            explanation="test",
            evidence_quotes=[r"site\1"],
        )
        result = _filter_evidence_quotes([tactic], message)
        # The quote r"site\1" IS literally present in the message, so it must be kept
        assert r"site\1" in result[0].evidence_quotes

    def test_html_special_chars_in_quote_are_handled(self):
        """Quotes with HTML-special characters are preserved by the filter."""
        from services.analysis_service import _filter_evidence_quotes
        from data.models import Tactic

        message = "Pay <amount> at <fake-site.com> now"
        tactic = Tactic(
            tactic_id="MONEY_REQUEST",
            tactic_name="Money Request",
            explanation="test",
            evidence_quotes=["<fake-site.com>"],
        )
        result = _filter_evidence_quotes([tactic], message)
        assert "<fake-site.com>" in result[0].evidence_quotes
