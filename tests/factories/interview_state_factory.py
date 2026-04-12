# tests/factories/interview_state_factory.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.answer import Answer
from domain.contracts.user.role import Role, RoleType
from domain.contracts.interview.interview_typeimport InterviewType
from domain.contracts.execution.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question_result import QuestionResult
from app.contracts.feedback_bundle import FeedbackBundle


# ---------------------------------------------------------
# QUESTION FACTORY
# ---------------------------------------------------------


def build_question(
    *,
    qid: str = "q1",
    qtype: QuestionType = QuestionType.CODING,
) -> Question:

    return Question(
        id=qid,
        area=InterviewArea.TECH_CODING,
        type=qtype,
        prompt="Write a function",
        difficulty=QuestionDifficulty.MEDIUM,
    )


# ---------------------------------------------------------
# BASE FACTORY
# ---------------------------------------------------------

def build_interview_state(
    *,
    questions=None,
    answers=None,
    current_question_index: int = 0,
) -> InterviewState:

    # default = 2 questions
    if questions is None:
        questions = [
            build_question(qid="q1"),
            build_question(qid="q2"),
        ]

    if answers is None:
        answers = [
            Answer(
                question_id=questions[0].id,
                content="print('hello')",
                attempt=1,
            )
        ]

    return InterviewState(
        interview_id="test-id",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="TestCorp",
        interview_type=InterviewType.TECHNICAL,
        language="en",
        questions=questions,
        answers=answers,
        current_question_index=current_question_index,
    )


# ---------------------------------------------------------
# STATE WITH EXECUTION (+ OPTIONAL QUALITY)
# ---------------------------------------------------------


def build_state_with_execution(
    *,
    passed_tests: int = 0,
    total_tests: int = 0,
    error: str | None = None,
    quality: str | None = None,
) -> InterviewState:

    state = build_interview_state()
    question = state.current_question

    # -----------------------------------------------------
    # STATUS + SUCCESS
    # -----------------------------------------------------

    if error:
        status = ExecutionStatus.RUNTIME_ERROR
        success = False

    elif total_tests > 0 and passed_tests == total_tests:
        status = ExecutionStatus.SUCCESS
        success = True

    elif total_tests > 0:
        status = ExecutionStatus.FAILED_TESTS
        success = False
        error = error or "Some tests failed"

    else:
        status = ExecutionStatus.INTERNAL_ERROR
        success = False
        error = error or "No tests detected"

    # -----------------------------------------------------
    # EXECUTION RESULT
    # -----------------------------------------------------

    execution = ExecutionResult(
        question_id=question.id,
        execution_type=ExecutionType.CODING,
        status=status,
        success=success,
        output="",
        error=error,
        passed_tests=passed_tests,
        total_tests=total_tests,
        execution_time_ms=10,
        test_results=[],
    )

    # -----------------------------------------------------
    # RESULT STRUCTURE
    # -----------------------------------------------------

    new_results = dict(state.results_by_question)

    new_results[question.id] = QuestionResult(
        question_id=question.id,
        execution=execution,
        evaluation=None,
        ai_hint=None,
        hint_level=None,
    )

    state = state.model_copy(update={"results_by_question": new_results})

    # -----------------------------------------------------
    # OPTIONAL FEEDBACK BUNDLE
    # -----------------------------------------------------

    if quality:
        state = state.model_copy(
            update={
                "last_feedback_bundle": FeedbackBundle(
                    blocks=[],
                    overall_severity="error",
                    overall_confidence=1.0,
                    overall_quality=quality,
                    markdown="",
                )
            }
        )

    return state


# ---------------------------------------------------------
# WRITTEN QUESTION STATE
# ---------------------------------------------------------


def build_written_question_state() -> InterviewState:

    question = build_question(qtype=QuestionType.WRITTEN)

    answer = Answer(
        question_id=question.id,
        content="REST is an architectural style...",
        attempt=1,
    )

    return InterviewState(
        interview_id="test-id",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="TestCorp",
        interview_type=InterviewType.TECHNICAL,
        language="en",
        questions=[question],
        answers=[answer],
        current_question_index=0,
    )
