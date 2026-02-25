# tests/ui/mappers/test_interview_state_mapper.py

import pytest

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.question import Question
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.question import QuestionType
from domain.contracts.role import Role
from domain.contracts.role import RoleType

from app.ui.mappers.interview_state_mapper import InterviewStateMapper


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def create_question(qid: str, area: str) -> Question:
    return Question(
        id=qid,
        area=area,
        type=QuestionType.WRITTEN,
        prompt=f"Question {qid}",
        difficulty=3,
    )


def create_evaluation(qid: str, score: float, weaknesses=None) -> QuestionEvaluation:
    return QuestionEvaluation(
        question_id=qid,
        score=score,
        max_score=100.0,
        feedback=f"Feedback {qid}",
        strengths=["clear explanation"],
        weaknesses=weaknesses or [],
        passed=score >= 60,
    )


def create_base_state() -> InterviewState:
    return InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="OpenAI",
        language="en",
    )


# ---------------------------------------------------------
# Session DTO tests
# ---------------------------------------------------------


def test_session_dto_in_progress_maps_current_question_correctly():

    state = create_base_state()
    state.progress = InterviewProgress.IN_PROGRESS
    state.questions = [
        create_question("q1", "Algorithms"),
        create_question("q2", "System Design"),
    ]
    state.current_question_index = 0

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.is_completed is False
    assert dto.current_question is not None
    assert dto.current_question.question_id == "q1"
    assert dto.current_question.index == 1
    assert dto.current_question.total == 2
    assert dto.current_area == "Algorithms"


def test_session_dto_completed_returns_no_current_question():

    state = create_base_state()
    state.progress = InterviewProgress.COMPLETED
    state.evaluations = [create_evaluation("q1", 80)]

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.is_completed is True
    assert dto.current_question is None
    assert dto.current_area is None


# ---------------------------------------------------------
# Final Report tests
# ---------------------------------------------------------


def test_final_report_aggregates_dimension_scores_by_area():

    state = create_base_state()
    state.questions = [
        create_question("q1", "Algorithms"),
        create_question("q2", "Algorithms"),
        create_question("q3", "System Design"),
    ]

    state.evaluations = [
        create_evaluation("q1", 80),
        create_evaluation("q2", 60),
        create_evaluation("q3", 90),
    ]

    mapper = InterviewStateMapper()
    report = mapper.to_final_report_dto(state)

    dimension_map = {d.name: d.score for d in report.dimension_scores}

    assert dimension_map["Algorithms"] == 70  # average of 80 and 60
    assert dimension_map["System Design"] == 90


def test_final_report_deduplicates_weaknesses():

    state = create_base_state()
    state.questions = [create_question("q1", "Algorithms")]

    state.evaluations = [
        create_evaluation(
            "q1", 50, weaknesses=["Too vague", "Too vague", "Lacks depth"]
        )
    ]

    mapper = InterviewStateMapper()
