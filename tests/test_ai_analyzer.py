"""Unit tests for ai/ai_analyzer.py.

All tests mock the Gemini client so no real API key is required.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors as genai_errors

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

    def test_fallback_reason_set_on_api_error(self):
        """fallback_reason must be populated so the diagnostic panel can display it."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("timeout")
        analyzer = AIAnalyzer(client=mock_client)
        result = analyzer.analyze("Some message.")
        assert result.fallback_reason != ""

    def test_fallback_debug_populated_on_error(self):
        """fallback_debug must contain sanitized error text (no secret values)."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("boom")
        analyzer = AIAnalyzer(client=mock_client)
        result = analyzer.analyze("Some message.")
        assert "boom" in result.fallback_debug

    def test_fallback_debug_redacts_api_key_pattern(self):
        """An AIza-style key in the error message must be redacted."""
        mock_client = MagicMock()
        fake_key = "AIzaSyFakeKeyABCDEFGHIJKLMNOPQRSTUVWXYZ1"
        mock_client.models.generate_content.side_effect = RuntimeError(
            f"Request failed with key={fake_key}"
        )
        analyzer = AIAnalyzer(client=mock_client)
        result = analyzer.analyze("Some message.")
        assert fake_key not in result.fallback_debug
        assert "<REDACTED_API_KEY>" in result.fallback_debug

    def test_parse_fail_sets_reason_parse_fail(self):
        """A response that cannot be parsed as JSON gets reason='parse_fail'."""
        client = _make_mock_client("Not JSON at all.")
        analyzer = AIAnalyzer(client=client)
        result = analyzer.analyze("Some message.")
        assert result.fallback_reason == "parse_fail"

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


class TestLazyClientInit:
    """Tests for the lazy-init fix: client must be resolved at analyze() time,
    not at construction time, so @st.cache_resource cannot freeze a None client."""

    def test_no_key_env_returns_fallback(self):
        """With no API key in environment, analyze() returns a safe fallback."""
        with patch.dict("os.environ", {}, clear=True):
            # Ensure GEMINI_API_KEY is absent
            import os
            os.environ.pop("GEMINI_API_KEY", None)
            analyzer = AIAnalyzer()  # constructed with no key in env
        # Even after construction the client should not be set yet
        assert analyzer._client is None
        result = analyzer.analyze("Test message.")
        assert result.is_fallback is True

    def test_placeholder_key_returns_fallback(self):
        """A placeholder key value is treated the same as no key."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "your_gemini_api_key_here"}):
            analyzer = AIAnalyzer()
        result = analyzer.analyze("Test message.")
        assert result.is_fallback is True

    def test_client_resolved_lazily_at_analyze_time(self):
        """Simulates the cache scenario: instance constructed before key is set,
        but analyze() is called after the key is available in the environment."""
        import os
        # Step 1: construct with no key (mimics @st.cache_resource creating the
        # instance before load_dotenv() has run)
        env_without_key = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
        with patch.dict("os.environ", env_without_key, clear=True):
            analyzer = AIAnalyzer()
        assert analyzer._client is None  # client not yet created

        # Step 2: key becomes available (load_dotenv() ran), and analyze() is called
        mock_client = _make_mock_client(_valid_ai_json(risk_level="High"))
        with patch("ai.ai_analyzer.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            mock_genai.types = __import__("google.genai", fromlist=["types"]).types
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-abc"}):
                result = analyzer.analyze("Urgent: claim your prize now!")

        assert result.risk_level == "High"
        assert result.is_fallback is False

    def test_client_created_once_and_reused(self):
        """Once _ensure_client() creates a client, subsequent analyze() calls
        reuse it without re-reading the environment."""
        mock_client = _make_mock_client(_valid_ai_json(risk_level="Medium"))
        with patch("ai.ai_analyzer.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            mock_genai.types = __import__("google.genai", fromlist=["types"]).types
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-abc"}):
                analyzer = AIAnalyzer()
                analyzer.analyze("First call.")
                analyzer.analyze("Second call.")
            # Client constructor called exactly once despite two analyze() calls
            assert mock_genai.Client.call_count == 1

    def test_genai_client_init_failure_returns_fallback(self):
        """If genai.Client() raises during lazy init, analyze() returns fallback."""
        with patch("ai.ai_analyzer.genai") as mock_genai:
            mock_genai.Client.side_effect = RuntimeError("network error")
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-abc"}):
                analyzer = AIAnalyzer()
                result = analyzer.analyze("Some message.")
        assert result.is_fallback is True

    def test_injected_client_bypasses_lazy_init(self):
        """An explicitly injected client (test scenario) is used directly and
        _ensure_client() never attempts to create a new one."""
        injected = _make_mock_client(_valid_ai_json(risk_level="Low"))
        with patch("ai.ai_analyzer.genai") as mock_genai:
            analyzer = AIAnalyzer(client=injected)
            analyzer.analyze("Some message.")
            mock_genai.Client.assert_not_called()


class TestClassifyError:
    """Unit tests for AIAnalyzer._classify_error — the error categorisation logic."""

    def test_404_api_error_is_model_not_found(self):
        exc = genai_errors.ClientError(
            404,
            {"error": {"code": 404, "status": "NOT_FOUND", "message": "model gone"}},
            None,
        )
        assert AIAnalyzer._classify_error(exc) == "model_not_found"

    def test_401_api_error_is_auth_error(self):
        exc = genai_errors.ClientError(
            401,
            {"error": {"code": 401, "status": "UNAUTHENTICATED", "message": "bad key"}},
            None,
        )
        assert AIAnalyzer._classify_error(exc) == "auth_error"

    def test_429_api_error_is_quota_exceeded(self):
        exc = genai_errors.ClientError(
            429,
            {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota"}},
            None,
        )
        assert AIAnalyzer._classify_error(exc) == "quota_exceeded"

    def test_value_error_is_parse_fail(self):
        exc = ValueError("Could not extract JSON from response")
        assert AIAnalyzer._classify_error(exc) == "parse_fail"

    def test_runtime_error_is_unexpected(self):
        exc = RuntimeError("something weird happened")
        assert AIAnalyzer._classify_error(exc) == "unexpected"


class TestSanitizeErrorMessage:
    """Unit tests for AIAnalyzer._sanitize_error_message."""

    def test_aiza_key_is_redacted(self):
        fake_key = "AIzaSyFakeKeyABCDEFGHIJKLMNOPQRSTUVWXYZ1"
        exc = RuntimeError(f"auth failed key={fake_key}")
        result = AIAnalyzer._sanitize_error_message(exc)
        assert fake_key not in result
        assert "<REDACTED_API_KEY>" in result

    def test_aq_token_is_redacted(self):
        fake_token = "AQ.AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"
        exc = RuntimeError(f"Bearer token={fake_token} rejected")
        result = AIAnalyzer._sanitize_error_message(exc)
        assert fake_token not in result
        assert "<REDACTED_TOKEN>" in result

    def test_normal_message_unchanged(self):
        exc = RuntimeError("connection timed out after 30s")
        result = AIAnalyzer._sanitize_error_message(exc)
        assert "connection timed out" in result

    def test_long_message_is_truncated(self):
        exc = RuntimeError("x" * 600)
        result = AIAnalyzer._sanitize_error_message(exc)
        assert len(result) <= 504  # 500 + len("…")


class TestRetry:
    """Tests for the transient-error retry logic in _call_api_with_retry.

    All tests use mock clients and patch time.sleep so no real delays occur.
    """

    @staticmethod
    def _make_503() -> genai_errors.ServerError:
        return genai_errors.ServerError(
            503,
            {"error": {"code": 503, "status": "UNAVAILABLE", "message": "overloaded"}},
            None,
        )

    def test_503_is_classified_transient(self):
        exc = self._make_503()
        assert AIAnalyzer._classify_error(exc) == "transient"

    def test_502_is_classified_transient(self):
        exc = genai_errors.ServerError(
            502,
            {"error": {"code": 502, "status": "UNAVAILABLE", "message": "bad gateway"}},
            None,
        )
        assert AIAnalyzer._classify_error(exc) == "transient"

    def test_transient_error_retried_then_succeeds(self):
        """First call raises 503; second call succeeds — analyze() returns real result."""
        exc_503 = self._make_503()
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            exc_503,
            MagicMock(text=_valid_ai_json(risk_level="High")),
        ]
        analyzer = AIAnalyzer(client=mock_client)
        with patch("ai.ai_analyzer.time.sleep"):
            result = analyzer.analyze("Test message.")
        assert result.is_fallback is False
        assert result.risk_level == "High"
        assert mock_client.models.generate_content.call_count == 2

    def test_transient_error_exhausts_retries_returns_fallback(self):
        """All 3 attempts (1 + 2 retries) raise 503 — analyze() returns fallback."""
        exc_503 = self._make_503()
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [exc_503, exc_503, exc_503]
        analyzer = AIAnalyzer(client=mock_client)
        with patch("ai.ai_analyzer.time.sleep"):
            result = analyzer.analyze("Test message.")
        assert result.is_fallback is True
        assert result.fallback_reason == "transient"
        assert mock_client.models.generate_content.call_count == 3

    def test_permanent_error_not_retried(self):
        """A 404 (permanent) is raised on the first attempt with no retry."""
        exc_404 = genai_errors.ClientError(
            404,
            {"error": {"code": 404, "status": "NOT_FOUND", "message": "model gone"}},
            None,
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = exc_404
        analyzer = AIAnalyzer(client=mock_client)
        with patch("ai.ai_analyzer.time.sleep") as mock_sleep:
            result = analyzer.analyze("Test message.")
        assert result.is_fallback is True
        assert result.fallback_reason == "model_not_found"
        mock_client.models.generate_content.assert_called_once()
        mock_sleep.assert_not_called()

    def test_auth_error_not_retried(self):
        """A 401 (permanent) is not retried."""
        exc_401 = genai_errors.ClientError(
            401,
            {"error": {"code": 401, "status": "UNAUTHENTICATED", "message": "bad key"}},
            None,
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = exc_401
        analyzer = AIAnalyzer(client=mock_client)
        with patch("ai.ai_analyzer.time.sleep") as mock_sleep:
            analyzer.analyze("Test message.")
        mock_client.models.generate_content.assert_called_once()
        mock_sleep.assert_not_called()

    def test_sleep_called_between_retries(self):
        """time.sleep is called once after the first 503 (not after permanent failure)."""
        exc_503 = self._make_503()
        mock_client = MagicMock()
        # Two 503s then success
        mock_client.models.generate_content.side_effect = [
            exc_503,
            exc_503,
            MagicMock(text=_valid_ai_json(risk_level="Low")),
        ]
        analyzer = AIAnalyzer(client=mock_client)
        with patch("ai.ai_analyzer.time.sleep") as mock_sleep:
            analyzer.analyze("Test message.")
        assert mock_sleep.call_count == 2
        # Backoff: first sleep 1s, second sleep 2s
        calls = [c.args[0] for c in mock_sleep.call_args_list]
        assert calls[0] == 1.0
        assert calls[1] == 2.0
