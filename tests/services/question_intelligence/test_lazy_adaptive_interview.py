# tests/services/question_intelligence/test_lazy_adaptive_interview.py

from unittest.mock import MagicMock

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.shared.action_type import ActionType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)
from services.question_intelligence.adaptive_interview_memory_bridge import (
    AdaptiveInterviewMemoryBridge,
)
from services.question_intelligence.lazy_adaptive_interview_service import (
    LazyAdaptiveInterviewService,
)
from app.graph.nodes.adaptive_navigation_node import AdaptiveNavigationNode
from app.graph.nodes.decision_node import DecisionNode
from app.graph.nodes.completion_node import completion_node
from app.contracts.feedback_bundle import FeedbackBundle
from domain.contracts.feedback.quality import Quality


def _written_question(area: InterviewArea, question_id: str) -> Question:

    return Question(
        id=question_id,
        area=area,
        type=QuestionType.WRITTEN,
        prompt=f"Prompt {area.value}",
        difficulty=QuestionDifficulty.MEDIUM,
    )


def test_generate_first_question_returns_single_question() -> None:

    area_builder = MagicMock()
    area_builder.build.return_value = (
        [_written_question(InterviewArea.TECH_BACKGROUND, "q-1")],
        InterviewRetrievalMemory(strong_domains=["theme_anchor:backend"]),
    )

    service = LazyAdaptiveInterviewService(area_builder=area_builder)

    questions, memory, planned = service.generate_first_question(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
    )

    assert len(questions) == 1
    assert len(planned) == 5
    assert memory.strong_domains


def test_memory_updater_records_evaluation_signals() -> None:

    updater = InterviewMemoryUpdater()
    question = _written_question(InterviewArea.TECH_DATABASE, "q-db")

    updated = updater.update_from_question_evaluation(
        memory=InterviewRetrievalMemory(),
        question=question,
        evaluation_score=0.4,
    )

    assert updated.weak_domains == [InterviewArea.TECH_DATABASE.value]
    assert updated.average_score == 0.4
    assert updated.question_count == 1
    assert len(updated.difficulty_history) == 1


def test_memory_bridge_updates_from_evaluation() -> None:

    question = _written_question(InterviewArea.TECH_CODING, "q-code")
    result = QuestionResult(
        question_id=question.id,
        evaluation=QuestionEvaluation(
            question_id=question.id,
            score=90,
            max_score=100,
            passed=True,
            feedback="Strong answer",
        ),
    )

    updated = AdaptiveInterviewMemoryBridge().update_from_question_result(
        memory=InterviewRetrievalMemory(),
        question=question,
        result=result,
    )

    assert updated.strong_domains == [InterviewArea.TECH_CODING.value]
    assert updated.average_score == 0.9


def test_adaptive_navigation_generates_next_question_on_next() -> None:

    lazy_service = MagicMock()
    lazy_service.generate_next_question.return_value = (
        _written_question(InterviewArea.TECH_TECHNICAL_KNOWLEDGE, "q-2"),
        InterviewRetrievalMemory(average_score=0.5, question_count=1),
    )

    node = AdaptiveNavigationNode(lazy_service=lazy_service)

    state = _build_adaptive_state(
        questions=[_written_question(InterviewArea.TECH_BACKGROUND, "q-1")],
        planned_areas=[
            InterviewArea.TECH_BACKGROUND.value,
            InterviewArea.TECH_TECHNICAL_KNOWLEDGE.value,
        ],
        intent=ActionType.NEXT,
    )

    new_state = node(state)

    assert len(new_state.questions) == 2
    assert new_state.current_question_index == 1
    assert new_state.retrieval_memory.question_count >= 0
    lazy_service.generate_next_question.assert_called_once()


def test_decision_node_uses_planned_areas_for_last_question() -> None:

    node = DecisionNode()

    state = _build_adaptive_state(
        questions=[_written_question(InterviewArea.TECH_BACKGROUND, "q-1")],
        planned_areas=[area.value for area in InterviewType.TECHNICAL.get_areas()],
    )

    state = state.model_copy(
        update={
            "last_feedback_bundle": FeedbackBundle(
                blocks=[],
                overall_severity="info",
                overall_confidence=1.0,
                overall_quality=Quality.CORRECT,
                markdown="",
            ),
        }
    )

    new_state = node(state)

    assert ActionType.NEXT in new_state.allowed_actions


def test_completion_waits_until_all_planned_questions_generated() -> None:

    state = _build_adaptive_state(
        questions=[_written_question(InterviewArea.TECH_BACKGROUND, "q-1")],
        planned_areas=[area.value for area in InterviewType.TECHNICAL.get_areas()],
        current_question_index=0,
    )

    incomplete = completion_node(
        state.model_copy(update={"awaiting_user_input": False}),
    )

    assert incomplete.is_completed is False


def _build_adaptive_state(
    *,
    questions: list[Question],
    planned_areas: list[str],
    current_question_index: int = 0,
    intent: ActionType | None = None,
):

    from domain.contracts.interview_state import InterviewState
    from domain.contracts.user.role import Role

    return InterviewState(
        interview_id="adaptive-test",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="TestCorp",
        interview_type=InterviewType.TECHNICAL,
        language="en",
        questions=questions,
        current_question_index=current_question_index,
        planned_areas=planned_areas,
        adaptive_interview_enabled=True,
        retrieval_memory=InterviewRetrievalMemory(),
        intent=intent,
    )
