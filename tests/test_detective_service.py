"""Unit tests for services/detective_service.py."""

import pytest
from data.models import DetectiveScenario
from services.detective_service import DetectiveService


@pytest.fixture
def service() -> DetectiveService:
    return DetectiveService()


@pytest.fixture
def scenario() -> DetectiveScenario:
    """A simple scenario with 3 correct answers out of 5 phrases."""
    return DetectiveScenario(
        scenario_id="test_scenario",
        title="Test Scenario",
        message_text="Test message text.",
        phrases=["phrase_0", "phrase_1", "phrase_2", "phrase_3", "phrase_4"],
        correct_phrase_indices=[1, 2, 4],  # 3 correct answers
        explanation="Test explanation.",
        tactic_id="URGENCY",
    )


class TestScoreAttempt:
    def test_all_correct_returns_100(self, service, scenario):
        result = service.score_attempt(scenario, selected_indices=[1, 2, 4])
        assert result.score == 100

    def test_no_selections_returns_0(self, service, scenario):
        result = service.score_attempt(scenario, selected_indices=[])
        assert result.score == 0

    def test_all_wrong_returns_0(self, service, scenario):
        # Selecting only incorrect phrases: penalty drives score to 0
        result = service.score_attempt(scenario, selected_indices=[0, 3])
        assert result.score == 0

    def test_partial_correct_no_false_positives(self, service, scenario):
        # Select 2 out of 3 correct answers, no false positives
        result = service.score_attempt(scenario, selected_indices=[1, 2])
        expected = round((2 / 3) * 100)  # 67
        assert result.score == expected

    def test_false_positives_apply_penalty(self, service, scenario):
        # 3/3 correct but 2 false positives = 100 - 20 = 80
        result = service.score_attempt(scenario, selected_indices=[1, 2, 4, 0, 3])
        assert result.score == 80

    def test_score_never_below_zero(self, service, scenario):
        # Many false positives should not produce negative score
        result = service.score_attempt(scenario, selected_indices=[0, 3])
        assert result.score >= 0

    def test_correct_count_reported(self, service, scenario):
        result = service.score_attempt(scenario, selected_indices=[1, 4])
        assert result.correct_count == 2

    def test_total_correct_reported(self, service, scenario):
        result = service.score_attempt(scenario, selected_indices=[])
        assert result.total_correct == 3

    def test_missed_indices_reported(self, service, scenario):
        result = service.score_attempt(scenario, selected_indices=[1])
        assert set(result.missed_indices) == {2, 4}

    def test_false_positive_indices_reported(self, service, scenario):
        result = service.score_attempt(scenario, selected_indices=[1, 0])
        assert result.false_positive_indices == [0]

    def test_perfect_score_feedback_message(self, service, scenario):
        result = service.score_attempt(scenario, selected_indices=[1, 2, 4])
        assert "Perfect" in result.feedback or "🏆" in result.feedback


class TestGetScenario:
    def test_returns_correct_scenario_by_id(self, service):
        scenario = service.get_scenario("parcel_delivery")
        assert scenario.scenario_id == "parcel_delivery"

    def test_unknown_id_returns_first_scenario(self, service):
        scenario = service.get_scenario("does_not_exist")
        all_scenarios = service.get_all_scenarios()
        assert scenario.scenario_id == all_scenarios[0].scenario_id

    def test_get_all_scenarios_returns_list(self, service):
        scenarios = service.get_all_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 1
