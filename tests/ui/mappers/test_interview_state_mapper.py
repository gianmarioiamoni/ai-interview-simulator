# tests/ui/mappers/test_interview_state_mapper.py

import pytest

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.interview.interview_progress import InterviewProgress
from domain.contracts.shared.performance_dimension import PerformanceDimension

from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from tests.factories.interview_state_factory import (
    build_interview_state,
    build_state_with_execution,
)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


def build_interview_evaluation(*, overall_score: float = 75.0) -> InterviewEvaluation:

    return InterviewEvaluation(
        overall_score=overall_score,
        raw_score=overall_score,
        adjusted_score=overall_score,
        executive_summary="Solid overall performance.",
        performance_dimensions=[
            PerformanceDimension(
                name="technical_accuracy",
                score=80.0,
                justification="Mostly correct answers.",
            )
        ],
        dimension_scores={"technical_accuracy": 80.0, "communication": 70.0},
        dimension_signals={"technical_accuracy": 0.8},
        level=InterviewLevel.STRONG,
        hire_decision=HireDecision.LEAN_HIRE,
        decision_explanation={"strengths": ["good fundamentals"]},
        hiring_probability=65.0,
        percentile_rank=70.0,
        percentile_explanation="Above average candidate.",
        gating_triggered=False,
        gating_reason=None,
        weighted_breakdown={"technical_accuracy": 40.0, "communication": 35.0},
        per_question_assessment=[],
        improvement_suggestions=["Practice system design."],
        confidence=Confidence(base=0.8, final=0.85),
    )


# ---------------------------------------------------------
# SESSION DTO
# ---------------------------------------------------------


def test_session_dto_in_progress_maps_current_question_correctly():

    state = build_interview_state().model_copy(
        update={"progress": InterviewProgress.IN_PROGRESS}
    )

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.session_id == state.interview_id
    assert dto.is_completed is False
    assert dto.current_question is not None
    assert dto.current_question.question_id == "q1"
    assert dto.current_question.index == 1
    assert dto.current_question.total == 2
    assert dto.current_area == "Coding"


def test_session_dto_second_question_advances_index():

    state = build_interview_state(current_question_index=1).model_copy(
        update={"progress": InterviewProgress.IN_PROGRESS}
    )

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.current_question.question_id == "q2"
    assert dto.current_question.index == 2


def test_session_dto_completed_returns_no_current_question():

    state = build_state_with_execution(passed_tests=2, total_tests=2)

    state = state.model_copy(
        update={
            "progress": InterviewProgress.COMPLETED,
            "current_question_index": len(state.questions),
        }
    )

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.is_completed is True
    assert dto.current_question is None
    assert dto.current_area is None


# ---------------------------------------------------------
# FINAL REPORT DTO
# ---------------------------------------------------------


def test_final_report_requires_interview_evaluation():

    state = build_interview_state()

    mapper = InterviewStateMapper()

    with pytest.raises(ValueError, match="Final evaluation is required"):
        mapper.to_final_report_dto(state)


def test_final_report_maps_evaluation_fields():

    state = build_state_with_execution(passed_tests=2, total_tests=2)

    evaluation = build_interview_evaluation(overall_score=75.0)
    state = state.model_copy(update={"interview_evaluation": evaluation})

    mapper = InterviewStateMapper()
    report = mapper.to_final_report_dto(state)

    assert report.overall_score == 75.0
    assert report.hire_decision == "Lean Hire"
    assert report.executive_summary == "Solid overall performance."
    assert report.role == state.role.type
    assert report.improvement_suggestions == ["Practice system design."]
    assert report.confidence == evaluation.confidence


def test_final_report_maps_dimension_scores():

    state = build_state_with_execution(passed_tests=1, total_tests=2)

    state = state.model_copy(
        update={"interview_evaluation": build_interview_evaluation()}
    )

    mapper = InterviewStateMapper()
    report = mapper.to_final_report_dto(state)

    dimension_map = {d.name: d.score for d in report.dimension_scores}

    assert dimension_map["Technical Accuracy"] == 80.0
    assert dimension_map["Communication"] == 70.0


def test_final_report_includes_question_assessments_from_results():

    state = build_state_with_execution(passed_tests=1, total_tests=2)

    state = state.model_copy(
        update={"interview_evaluation": build_interview_evaluation()}
    )

    mapper = InterviewStateMapper()
    report = mapper.to_final_report_dto(state)

    assert len(report.question_assessments) == 1

    assessment = report.question_assessments[0]

    assert assessment.question_id == "q1"
    assert assessment.passed_tests == 1
    assert assessment.total_tests == 2
    assert assessment.score == 50.0
