# tests/performance/slo_r.py
# EPIC-V13-09 C3 — SLO-R harness: session_close entry → report exit (AR-03, MEAS-05).

from __future__ import annotations

from app.graph.nodes.report_node import report_node
from app.graph.nodes.session_close_node import session_close_node
from domain.contracts.interview.answer import Answer
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.user.role import RoleType
from tests.domain.contracts.report.conftest import (
    make_context_profile,
    make_scoring_narrative,
    make_scoring_snapshot,
)
from tests.performance.helpers import measure_wall_clock_ms

# Implementation Plan §3 / AR-03 absolute target (load gate reuses in C7).
SLO_R_TARGET_MS = 3000.0
_DEFAULT_WRITTEN_QUESTION_COUNT = 5


def build_completed_state_for_slo_r(
    *,
    n_questions: int = _DEFAULT_WRITTEN_QUESTION_COUNT,
    interview_id: str = "slo-r-session",
    candidate_identity_id: str = "slo-r-candidate",
) -> InterviewState:
    """Completed written-heavy state ready for close→report (no longitudinal/UI/DTO)."""
    questions = [
        Question(
            id=f"q{i}",
            area=InterviewArea.TECH_CODING,
            type=QuestionType.WRITTEN,
            prompt=f"Written question {i}",
            difficulty=QuestionDifficulty.MEDIUM,
        )
        for i in range(n_questions)
    ]
    answers = [
        Answer(question_id=f"q{i}", content=f"Answer for question {i}", attempt=1)
        for i in range(n_questions)
    ]
    results_by_question: dict[str, QuestionResult] = {}
    for i in range(n_questions):
        qid = f"q{i}"
        results_by_question[qid] = QuestionResult(
            question_id=qid,
            evaluation=QuestionEvaluation(
                question_id=qid,
                score=90.0,
                max_score=100.0,
                passed=True,
                feedback="Solid answer.",
                strengths=["Clear"],
                weaknesses=[],
            ),
        )

    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="SLO-R",
        language="en",
        questions=questions,
        interview_id=interview_id,
    )
    return state.model_copy(
        update={
            "is_completed": True,
            "answers": answers,
            "current_question_index": max(n_questions - 1, 0),
            "candidate_identity_id": candidate_identity_id,
            "results_by_question": results_by_question,
            "scoring_snapshot": make_scoring_snapshot(),
            "scoring_narrative": make_scoring_narrative(),
            "context_profile": make_context_profile(),
        }
    )


def run_close_report_span(state: InterviewState) -> InterviewState:
    """
    Contiguous AR-03 span: ``session_close`` entry → ``report`` exit.

    Does not invoke ``longitudinal_update``, UI builders, or FinalReportDTO mapping
    (MEAS-05).
    """
    return report_node(session_close_node(state))


def measure_close_report_ms(
    state: InterviewState | None = None,
) -> tuple[InterviewState, float]:
    """Wall-clock measure of close→report under stub/harness conditions (AR-03)."""
    base = state if state is not None else build_completed_state_for_slo_r()
    return measure_wall_clock_ms(lambda: run_close_report_span(base))
