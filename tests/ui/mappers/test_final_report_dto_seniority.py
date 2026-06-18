# tests/ui/mappers/test_final_report_dto_seniority.py

import pytest

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.shared.performance_dimension import PerformanceDimension

from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from tests.factories.interview_state_factory import build_state_with_execution


def _build_evaluation() -> InterviewEvaluation:
    return InterviewEvaluation(
        overall_score=80.0,
        raw_score=80.0,
        adjusted_score=80.0,
        executive_summary="Good performance.",
        performance_dimensions=[
            PerformanceDimension(
                name="technical_accuracy",
                score=80.0,
                justification="Correct answers.",
            )
        ],
        dimension_scores={"technical_accuracy": 80.0},
        dimension_signals={"technical_accuracy": 0.8},
        level=InterviewLevel.STRONG,
        hire_decision=HireDecision.LEAN_HIRE,
        decision_explanation={"strengths": ["good fundamentals"]},
        hiring_probability=70.0,
        percentile_rank=75.0,
        percentile_explanation="Above average.",
        gating_triggered=False,
        gating_reason=None,
        weighted_breakdown={"technical_accuracy": 40.0},
        per_question_assessment=[],
        improvement_suggestions=[],
        confidence=Confidence(base=0.8, final=0.85),
    )


class TestFinalReportDTOSeniority:

    def test_report_includes_seniority_level_from_state(self):
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        state = state.model_copy(update={
            "interview_evaluation": _build_evaluation(),
            "seniority_level": "senior",
        })

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.seniority_level == "senior"

    def test_report_seniority_junior(self):
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        state = state.model_copy(update={
            "interview_evaluation": _build_evaluation(),
            "seniority_level": "junior",
        })

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.seniority_level == "junior"

    def test_report_seniority_defaults_to_state_mid(self):
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        state = state.model_copy(update={
            "interview_evaluation": _build_evaluation(),
        })

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.seniority_level == "mid"

    def test_existing_report_fields_unaffected(self):
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        evaluation = _build_evaluation()
        state = state.model_copy(update={
            "interview_evaluation": evaluation,
            "seniority_level": "senior",
        })

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.overall_score == 80.0
        assert report.hire_decision == "Lean Hire"
        assert report.role == state.role.type
