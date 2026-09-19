"""Tests for the new AnalysisService behaviours added in the P0/P1 audit.

Covers:
  - evidence quote filtering (_filter_evidence_quotes)
  - learn_tactic_id derivation (_derive_learn_tactic_id)
  - end-to-end run() with a mock analyzer
"""

import json
from unittest.mock import MagicMock

import pytest

from data.models import AnalysisResult, Tactic
from services.analysis_service import (
    AnalysisService,
    _derive_learn_tactic_id,
    _filter_evidence_quotes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tactic(tactic_id: str, quotes: list[str] | None = None) -> Tactic:
    return Tactic(
        tactic_id=tactic_id,
        tactic_name=tactic_id,
        explanation="test explanation",
        evidence_quotes=quotes or [],
    )


def _make_result(
    tactics: list[Tactic],
    learn_tactic_id: str = "",
    risk_level: str = "Low",
    is_fallback: bool = False,
) -> AnalysisResult:
    return AnalysisResult(
        risk_level=risk_level,
        risk_summary="test",
        tactics=tactics,
        recommended_actions=["Be careful."],
        learn_tactic_id=learn_tactic_id,
        is_fallback=is_fallback,
    )


def _mock_analyzer(result: AnalysisResult) -> MagicMock:
    mock = MagicMock()
    mock.analyze.return_value = result
    return mock


# ---------------------------------------------------------------------------
# _filter_evidence_quotes
# ---------------------------------------------------------------------------

class TestFilterEvidenceQuotes:
    MESSAGE = "Pay now at fake-link.net within 24 hours or your account will be blocked."

    def test_valid_quote_is_kept(self):
        tactics = [_make_tactic("URGENCY", quotes=["within 24 hours"])]
        result = _filter_evidence_quotes(tactics, self.MESSAGE)
        assert result[0].evidence_quotes == ["within 24 hours"]

    def test_hallucinated_quote_is_removed(self):
        # This phrase does not appear in MESSAGE
        tactics = [_make_tactic("FEAR", quotes=["Your identity has been stolen"])]
        result = _filter_evidence_quotes(tactics, self.MESSAGE)
        assert result[0].evidence_quotes == []

    def test_mix_of_valid_and_invalid_quotes(self):
        tactics = [_make_tactic("MONEY_REQUEST", quotes=["Pay now", "Send ₹500 immediately"])]
        result = _filter_evidence_quotes(tactics, self.MESSAGE)
        assert result[0].evidence_quotes == ["Pay now"]

    def test_empty_string_quote_is_removed(self):
        tactics = [_make_tactic("URGENCY", quotes=["", "within 24 hours"])]
        result = _filter_evidence_quotes(tactics, self.MESSAGE)
        assert "" not in result[0].evidence_quotes
        assert "within 24 hours" in result[0].evidence_quotes

    def test_tactic_with_no_quotes_is_unchanged(self):
        tactics = [_make_tactic("SUSPICIOUS_LINK", quotes=[])]
        result = _filter_evidence_quotes(tactics, self.MESSAGE)
        assert result[0].evidence_quotes == []

    def test_multiple_tactics_filtered_independently(self):
        tactics = [
            _make_tactic("URGENCY", quotes=["within 24 hours", "FAKE QUOTE"]),
            _make_tactic("FEAR", quotes=["your account will be blocked", "NOT IN MESSAGE"]),
        ]
        result = _filter_evidence_quotes(tactics, self.MESSAGE)
        assert result[0].evidence_quotes == ["within 24 hours"]
        assert result[1].evidence_quotes == ["your account will be blocked"]


# ---------------------------------------------------------------------------
# _derive_learn_tactic_id
# ---------------------------------------------------------------------------

class TestDeriveLearnTacticId:
    def test_returns_credential_request_first(self):
        tactics = [
            _make_tactic("URGENCY"),
            _make_tactic("CREDENTIAL_REQUEST"),
            _make_tactic("REWARD"),
        ]
        assert _derive_learn_tactic_id(tactics) == "CREDENTIAL_REQUEST"

    def test_returns_money_request_over_urgency(self):
        tactics = [_make_tactic("URGENCY"), _make_tactic("MONEY_REQUEST")]
        assert _derive_learn_tactic_id(tactics) == "MONEY_REQUEST"

    def test_returns_first_tactic_when_none_in_priority(self):
        # Custom tactic ID not in priority list — falls back to first
        tactics = [_make_tactic("UNKNOWN_FUTURE_TACTIC")]
        assert _derive_learn_tactic_id(tactics) == "UNKNOWN_FUTURE_TACTIC"

    def test_single_tactic_returns_that_tactic(self):
        tactics = [_make_tactic("JOB_SCAM")]
        assert _derive_learn_tactic_id(tactics) == "JOB_SCAM"

    def test_authority_returned_before_urgency(self):
        tactics = [_make_tactic("URGENCY"), _make_tactic("AUTHORITY")]
        assert _derive_learn_tactic_id(tactics) == "AUTHORITY"


# ---------------------------------------------------------------------------
# AnalysisService.run() integration
# ---------------------------------------------------------------------------

class TestAnalysisServiceRun:
    def test_evidence_quotes_validated_before_return(self):
        """Hallucinated quotes not in the message are stripped before the result reaches the UI."""
        tactics = [_make_tactic("URGENCY", quotes=["within 24 hours", "FAKE QUOTE NOT IN MSG"])]
        result = _make_result(tactics, risk_level="Low")
        service = AnalysisService(_mock_analyzer(result))
        out, err = service.run("Act within 24 hours or face consequences.")
        assert err is None
        assert "FAKE QUOTE NOT IN MSG" not in out.tactics[0].evidence_quotes
        assert "within 24 hours" in out.tactics[0].evidence_quotes

    def test_learn_tactic_id_derived_when_ai_leaves_it_empty(self):
        tactics = [_make_tactic("CREDENTIAL_REQUEST"), _make_tactic("URGENCY")]
        result = _make_result(tactics, learn_tactic_id="", risk_level="High")
        service = AnalysisService(_mock_analyzer(result))
        out, err = service.run("Enter your OTP immediately or account locked.")
        assert err is None
        assert out.learn_tactic_id == "CREDENTIAL_REQUEST"

    def test_learn_tactic_id_from_ai_is_preserved_when_present(self):
        tactics = [_make_tactic("URGENCY")]
        result = _make_result(tactics, learn_tactic_id="URGENCY", risk_level="Low")
        service = AnalysisService(_mock_analyzer(result))
        out, err = service.run("Act now, only 1 hour left to respond.")
        assert err is None
        assert out.learn_tactic_id == "URGENCY"

    def test_fallback_result_passes_through_unchanged(self):
        result = _make_result([], is_fallback=True, risk_level="Unknown")
        service = AnalysisService(_mock_analyzer(result))
        out, err = service.run("Something suspicious in this message text.")
        assert err is None
        assert out.is_fallback is True
        assert out.risk_level == "Unknown"

    def test_short_input_returns_validation_error(self):
        service = AnalysisService(_mock_analyzer(_make_result([])))
        out, err = service.run("short")
        assert out is None
        assert err is not None

    def test_risk_escalated_when_credential_request_present(self):
        """Rule-based escalation overrides AI-returned Low risk when CREDENTIAL_REQUEST detected."""
        tactics = [_make_tactic("CREDENTIAL_REQUEST", quotes=["Enter your OTP"])]
        result = _make_result(tactics, risk_level="Low")
        service = AnalysisService(_mock_analyzer(result))
        out, err = service.run("Enter your OTP now to verify your account immediately.")
        assert err is None
        assert out.risk_level == "High"

    def test_authority_tactic_escalates_to_medium(self):
        """AUTHORITY is now high-severity: single occurrence -> at least Medium."""
        tactics = [_make_tactic("AUTHORITY", quotes=["Income Tax Department"])]
        result = _make_result(tactics, risk_level="Low")
        service = AnalysisService(_mock_analyzer(result))
        out, err = service.run("Income Tax Department: your refund is ready. Click to claim.")
        assert err is None
        assert out.risk_level in ("Medium", "High")
