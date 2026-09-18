"""Analysis service — orchestrates the DETECT → EXPLAIN pipeline.

AnalysisService is the single entry point for the UI layer.
It coordinates input validation, AI analysis, and risk-level override.
"""

from ai.ai_analyzer import AIAnalyzer
from data.models import AnalysisResult
from services.risk_assessor import assess_risk, escalate_risk
from services.validator import sanitize_input, validate_length


class AnalysisService:
    """Orchestrates the full message analysis pipeline.

    Usage:
        service = AnalysisService(AIAnalyzer())
        result, error = service.run(raw_text)
        if error:
            show_error(error)
        else:
            show_result(result)
    """

    def __init__(self, analyzer: AIAnalyzer) -> None:
        """Initialize with an AIAnalyzer instance.

        Args:
            analyzer: The AI analyzer to use for semantic analysis.
                      Can be a mock for testing.
        """
        self._analyzer = analyzer

    def run(self, raw_text: str) -> tuple[AnalysisResult | None, str | None]:
        """Run the full analysis pipeline on raw user input.

        Steps:
          1. Validate length of input.
          2. Sanitize (strip HTML, normalize whitespace).
          3. Run AI analysis.
          4. Apply rule-based risk override if the rules indicate higher risk.

        Args:
            raw_text: Unvalidated text pasted by the user.

        Returns:
            A tuple of (AnalysisResult, None) on success,
            or (None, error_message_string) on validation failure.
        """
        is_valid, error_msg = validate_length(raw_text)
        if not is_valid:
            return None, error_msg

        clean_text = sanitize_input(raw_text)

        result = self._analyzer.analyze(clean_text)

        # Apply rule-based safety net: never downgrade, only escalate.
        if not result.is_fallback:
            rule_risk = assess_risk(result.tactics)
            result.risk_level = escalate_risk(result.risk_level, rule_risk)

        return result, None
