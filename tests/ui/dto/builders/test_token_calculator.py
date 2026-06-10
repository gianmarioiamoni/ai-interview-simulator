# tests/ui/dto/builders/test_token_calculator.py

from domain.contracts.interview.interview_metrics import InterviewMetrics
from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.user.role import Role, RoleType

from app.ui.dto.builders.token_calculator import TokenCalculator


def test_prefers_interview_metrics_when_available() -> None:
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="AuditCo",
        language="en",
        interview_metrics=InterviewMetrics(
            total_calls=3,
            total_input_tokens=100,
            total_output_tokens=50,
            total_tokens=999,
            total_retries=0,
            avg_latency_ms=100.0,
            operations=[],
        ),
        results_by_question={
            "q1": QuestionResult(
                question_id="q1",
                evaluation=QuestionEvaluation(
                    question_id="q1",
                    score=80.0,
                    max_score=100.0,
                    feedback="ok",
                    passed=True,
                    tokens_used=10,
                ),
            )
        },
    )

    assert TokenCalculator().calculate(state) == 999


def test_falls_back_to_evaluation_tokens_used() -> None:
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="AuditCo",
        language="en",
        results_by_question={
            "q1": QuestionResult(
                question_id="q1",
                evaluation=QuestionEvaluation(
                    question_id="q1",
                    score=80.0,
                    max_score=100.0,
                    feedback="ok",
                    passed=True,
                    tokens_used=42,
                ),
            )
        },
    )

    assert TokenCalculator().calculate(state) == 42
