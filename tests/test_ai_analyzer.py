"""Unit tests for ai/ai_analyzer.py.

All tests mock the Gemini client so no real API key is required.
"""

import json
from unittest.mock import MagicMock

import pytest

from ai.ai_analyzer import AIAnalyzer
from data.models import AnalysisResult, Tactic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_client(content: str) -> MagicMock:
    """Return a mock Gemini client that returns `content` from models.generate_content."""
    mock_response = MagicMock()
    mock_response.text = content

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


def _valid_ai_json(
    risk_level: str = "High",
    tactics: list | None = None,
    recommended_actions: list | None = None,
    learn_tactic_id: str = "URGENCY",
) -> str:
    if tactics is None:
        tactics = [
            {
                "tactic_id": "URGENCY",
                "tactic_name": "Urgency / Time Pressure",
                "explanation": "Creates artificial deadline.",
                "evidence_quotes": ["within 24 hours"],
            }
        ]
    if recommended_actions is None:
        recommended_actions = ["Do not click any links.", "Verify through official channels."]
    return json.dumps(
        {
            "risk_level": risk_level,
            "risk_summary": "This message contains several High Risk signals.",
            "tactics": tactics,
            "recommended_actions": recommended_actions,
            "learn_tactic_id": learn_tactic_id,
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAIAnalyzer:
    def test_valid_json_returns_correct_risk_level(self):
        client = _make_mock_client(_valid_ai_json(risk_level="High"))
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Your parcel expires in 24 hours.")
        assert result.risk_level == "High"

    def test_valid_json_returns_tactics(self):
        client = _make_mock_client(_valid_ai_json())
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Some message.")
        assert len(result.tactics) == 1
        assert result.tactics[0].tactic_id == "URGENCY"

    def test_valid_json_returns_evidence_quotes(self):
        client = _make_mock_client(_valid_ai_json())
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Act within 24 hours.")
        assert "within 24 hours" in result.tactics[0].evidence_quotes

    def test_json_embedded_in_prose_is_extracted(self):
        prose_with_json = (
            "Here is my analysis:\n"
            + _valid_ai_json(risk_level="Medium")
            + "\nLet me know if you need more."
        )
        client = _make_mock_client(prose_with_json)
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Some message.")
        assert result.risk_level == "Medium"

    def test_missing_risk_level_returns_unknown(self):
        bad_json = json.dumps(
            {
                "risk_summary": "test",
                "tactics": [],
                "recommended_actions": [],
                "learn_tactic_id": "",
            }
        )
        client = _make_mock_client(bad_json)
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Some message.")
        assert result.risk_level == "Unknown"

    def test_unknown_tactic_id_is_skipped(self):
        json_with_bad_tactic = json.dumps(
            {
                "risk_level": "High",
                "risk_summary": "test",
                "tactics": [
                    {
                        "tactic_id": "NONEXISTENT_TACTIC",
                        "tactic_name": "Something",
                        "explanation": "Explanation.",
                        "evidence_quotes": [],
                    }
                ],
                "recommended_actions": ["Be careful."],
                "learn_tactic_id": "",
            }
        )
        client = _make_mock_client(json_with_bad_tactic)
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Some message.")
        assert result.tactics == []

    def test_api_exception_returns_fallback(self):
        # Simulate any API failure — analyze() catches all exceptions and returns fallback
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("connection failed")
        analyzer = AIAnalyzer(client=mock_client)
        result = analyzer.analyze("Some message.")
        assert result.is_fallback is True
        assert result.risk_level == "Unknown"

    def test_empty_tactics_list_is_valid(self):
        empty_tactics_json = json.dumps(
            {
                "risk_level": "Low",
                "risk_summary": "No significant warning signs detected.",
                "tactics": [],
                "recommended_actions": ["Stay cautious online."],
                "learn_tactic_id": "",
            }
        )
        client = _make_mock_client(empty_tactics_json)
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Hi, your appointment is tomorrow.")
        assert result.risk_level == "Low"
        assert result.tactics == []
        assert result.is_fallback is False

    def test_completely_unparseable_response_returns_fallback(self):
        client = _make_mock_client("Sorry, I cannot analyze this.")
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Some message.")
        assert result.is_fallback is True

    def test_fallback_result_has_generic_actions(self):
        # Simulate any API failure — fallback result must always include safe actions
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("timeout")
        analyzer = AIAnalyzer(client=mock_client)
        result = analyzer.analyze("Some message.")
        assert len(result.recommended_actions) > 0

    def test_recommended_actions_returned_from_ai(self):
        actions = ["Do not click links.", "Contact your bank directly."]
        client = _make_mock_client(_valid_ai_json(recommended_actions=actions))
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Some message.")
        assert result.recommended_actions == actions
