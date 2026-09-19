"""Detective Mode service — scenario loading and attempt scoring."""

from data.models import DetectiveResult, DetectiveScenario
from data.scenarios import SCENARIOS


class DetectiveService:
    """Manages Detective Mode scenarios and scores user attempts.

    Usage:
        service = DetectiveService()
        scenario = service.get_scenario("parcel_delivery")
        result = service.score_attempt(scenario, selected_indices=[1, 2, 4])
    """

    def get_all_scenarios(self) -> list[DetectiveScenario]:
        """Return all available Detective Mode scenarios."""
        return list(SCENARIOS)

    def get_scenario(self, scenario_id: str) -> DetectiveScenario:
        """Return a scenario by its ID, or the first scenario as a fallback.

        Args:
            scenario_id: The unique ID of the desired scenario.

        Returns:
            The matching DetectiveScenario, or the first scenario if not found.
        """
        for scenario in SCENARIOS:
            if scenario.scenario_id == scenario_id:
                return scenario
        return SCENARIOS[0]

    def score_attempt(
        self,
        scenario: DetectiveScenario,
        selected_indices: list[int],
    ) -> DetectiveResult:
        """Score a user's Detective Mode submission.

        Scoring logic:
          - Base score = (correct_selections / total_correct) * 100
          - Each false positive (incorrect selection) deducts 10 points
          - Score is clamped to the range [0, 100]

        Args:
            scenario:         The scenario the user was attempting.
            selected_indices: Indices of phrases the user checked as suspicious.

        Returns:
            A DetectiveResult with score, counts, and feedback text.
        """
        correct_set = set(scenario.correct_phrase_indices)
        selected_set = set(selected_indices)

        correct_selections = correct_set.intersection(selected_set)
        false_positives = selected_set - correct_set
        missed = correct_set - selected_set

        total_correct = len(correct_set)
        correct_count = len(correct_selections)

        if total_correct == 0:
            base_score = 100
        else:
            base_score = round((correct_count / total_correct) * 100)

        penalty = len(false_positives) * 10
        score = max(0, min(100, base_score - penalty))

        feedback = self._build_feedback(score, correct_count, total_correct, len(false_positives))

        return DetectiveResult(
            score=score,
            correct_count=correct_count,
            total_correct=total_correct,
            missed_indices=sorted(missed),
            false_positive_indices=sorted(false_positives),
            feedback=feedback,
        )

    @staticmethod
    def _build_feedback(
        score: int,
        correct_count: int,
        total_correct: int,
        false_positive_count: int,
    ) -> str:
        """Build a plain-English feedback message for the user."""
        if score == 100:
            return "🏆 Perfect score! You identified all the suspicious clues correctly."
        if score >= 70:
            msg = f"👍 Good work! You spotted {correct_count} out of {total_correct} suspicious clues."
        elif score >= 40:
            msg = f"🤔 Not bad — you found {correct_count} out of {total_correct} clues."
        else:
            msg = f"💡 Keep practising — you found {correct_count} out of {total_correct} clues."

        if false_positive_count > 0:
            msg += (
                f" You also selected {false_positive_count} phrase(s) that "
                "were not suspicious — watch out for false alarms."
            )
        return msg
