"""Unit tests for services/risk_assessor.py."""

import pytest
from data.models import Tactic
from services.risk_assessor import assess_risk, escalate_risk


def make_tactic(tactic_id: str) -> Tactic:
    """Helper to create a minimal Tactic for testing."""
    return Tactic(
        tactic_id=tactic_id,
        tactic_name=tactic_id,
        explanation="test",
        evidence_quotes=[],
    )


class TestAssessRisk:
    def test_empty_list_returns_low(self):
        assert assess_risk([]) == "Low"

    def test_single_urgency_returns_low(self):
        assert assess_risk([make_tactic("URGENCY")]) == "Low"

    def test_two_low_severity_returns_low(self):
        tactics = [make_tactic("URGENCY"), make_tactic("REWARD")]
        assert assess_risk(tactics) == "Low"

    def test_three_low_severity_returns_medium(self):
        tactics = [make_tactic("URGENCY"), make_tactic("REWARD"), make_tactic("INFO_HARVEST")]
        assert assess_risk(tactics) == "Medium"

    def test_single_fear_returns_medium(self):
        # FEAR is high-severity but not auto-High
        assert assess_risk([make_tactic("FEAR")]) == "Medium"

    def test_single_suspicious_link_returns_medium(self):
        assert assess_risk([make_tactic("SUSPICIOUS_LINK")]) == "Medium"

    def test_credential_request_alone_returns_high(self):
        assert assess_risk([make_tactic("CREDENTIAL_REQUEST")]) == "High"

    def test_money_request_alone_returns_high(self):
        assert assess_risk([make_tactic("MONEY_REQUEST")]) == "High"

    def test_two_high_severity_tactics_returns_high(self):
        tactics = [make_tactic("FEAR"), make_tactic("SUSPICIOUS_LINK")]
        assert assess_risk(tactics) == "High"

    def test_mixed_low_and_high_severity(self):
        # REWARD (low) + URGENCY (low) + INFO_HARVEST (low) = Medium (3 low)
        tactics = [make_tactic("REWARD"), make_tactic("URGENCY"), make_tactic("INFO_HARVEST")]
        assert assess_risk(tactics) == "Medium"

    def test_impersonation_with_urgency_is_low(self):
        # IMPERSONATION and URGENCY are both low-severity (2 = Low)
        tactics = [make_tactic("IMPERSONATION"), make_tactic("URGENCY")]
        assert assess_risk(tactics) == "Low"


class TestEscalateRisk:
    def test_rule_higher_than_ai(self):
        assert escalate_risk("Low", "High") == "High"

    def test_ai_higher_than_rule(self):
        assert escalate_risk("High", "Low") == "High"

    def test_equal_levels(self):
        assert escalate_risk("Medium", "Medium") == "Medium"

    def test_unknown_ai_level_uses_rule(self):
        # Unknown maps to severity 1 (Medium equivalent)
        result = escalate_risk("Unknown", "High")
        assert result == "High"

    def test_rule_medium_does_not_downgrade_ai_high(self):
        assert escalate_risk("High", "Medium") == "High"
