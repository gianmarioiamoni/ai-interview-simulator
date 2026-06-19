# tests/graph/nodes/test_question_node.py

from unittest.mock import Mock

from app.graph.nodes.question_node import build_question_node
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.question.question import QuestionType


def test_question_node_no_question():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    state = state.model_copy(update={"current_question_index": -1})

    new_state = node(state)

    assert new_state == state


def test_question_node_prevents_double_processing():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()

    state = state.model_copy(
        update={
            "chat_history": ["already processed"],
            "current_question_index": 0,
        }
    )

    new_state = node(state)

    assert new_state.chat_history == state.chat_history
    llm.invoke.assert_not_called()


def test_question_node_humanizer_disabled():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    state = state.model_copy(update={"enable_humanizer": False})

    question = state.current_question

    new_state = node(state)

    assert question.prompt in new_state.chat_history
    assert len(new_state.chat_history) == len(state.chat_history) + 1


def test_question_node_non_written():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()

    q = state.current_question.model_copy(update={"type": QuestionType.CODING})

    state = state.model_copy(update={"questions": [q]})

    new_state = node(state)

    assert q.prompt in new_state.chat_history
    assert len(new_state.chat_history) == len(state.chat_history) + 1


def test_question_node_database_stores_prompt_only_schema_owned_by_display():
    """DATABASE question_node stores raw prompt; DisplaySection owns schema rendering."""
    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(
        update={
            "type": QuestionType.DATABASE,
            "db_schema": "CREATE TABLE employees (id INT, name TEXT);",
        }
    )
    state = state.model_copy(update={"questions": [q]})

    new_state = node(state)

    history_entry = new_state.chat_history[-1]
    assert history_entry == q.prompt
    assert "Database Schema" not in history_entry
    assert new_state.question_display_text == q.prompt


def test_question_node_database_no_schema_stores_prompt():
    """DATABASE question without db_schema stores prompt only."""
    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(
        update={"type": QuestionType.DATABASE, "db_schema": None}
    )
    state = state.model_copy(update={"questions": [q]})

    new_state = node(state)

    assert new_state.chat_history[-1] == q.prompt
    assert "Database Schema" not in new_state.chat_history[-1]


def test_question_node_coding_stores_prompt_only():
    """CODING questions store raw prompt only; no schema injection."""
    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.CODING})
    state = state.model_copy(update={"questions": [q]})

    new_state = node(state)

    assert new_state.chat_history[-1] == q.prompt
    assert "Database Schema" not in new_state.chat_history[-1]


def test_question_node_database_humanizer_disabled_stores_prompt_only():
    """Even with humanizer disabled, DATABASE schema is not injected by question_node."""
    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(
        update={
            "type": QuestionType.DATABASE,
            "db_schema": "CREATE TABLE orders (id INT);",
        }
    )
    state = state.model_copy(
        update={"questions": [q], "enable_humanizer": False}
    )

    new_state = node(state)

    history_entry = new_state.chat_history[-1]
    assert history_entry == q.prompt
    assert "Database Schema" not in history_entry


def test_question_node_humanized():

    llm = Mock()
    llm.invoke.return_value = Mock(
        content='{"decision": "plain_question", "message": "humanized question"}'
    )

    node = build_question_node(llm)

    state = build_interview_state()

    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})

    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "enable_humanizer": True,
        }
    )

    new_state = node(state)

    assert "humanized question" in new_state.chat_history
    assert len(new_state.chat_history) == 1
    llm.invoke.assert_called_once()


# ---------------------------------------------------------
# question_display_text
# ---------------------------------------------------------


def test_question_node_sets_question_display_text_humanized():
    llm = Mock()
    llm.invoke.return_value = Mock(
        content='{"decision": "direct_question", "message": "Conversational intro to the question."}'
    )

    node = build_question_node(llm)
    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "enable_humanizer": True,
        }
    )

    new_state = node(state)

    assert new_state.question_display_text == "Conversational intro to the question."


def test_question_node_sets_question_display_text_fallback_when_humanizer_disabled():
    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "enable_humanizer": False,
        }
    )

    new_state = node(state)

    assert new_state.question_display_text == q.prompt
    llm.invoke.assert_not_called()


def test_question_node_sets_question_display_text_raw_for_non_written():
    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.CODING})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
        }
    )

    new_state = node(state)

    assert new_state.question_display_text == q.prompt
    llm.invoke.assert_not_called()


def test_question_display_text_none_on_fresh_state():
    state = build_interview_state()
    assert state.question_display_text is None


def test_question_display_text_reset_on_create_initial():
    from domain.contracts.user.role import RoleType
    from domain.contracts.interview.interview_type import InterviewType
    from domain.contracts.interview_state import InterviewState

    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="Acme",
        language="en",
        questions=[],
        interview_id="test-reset",
    )
    assert state.question_display_text is None


# ---------------------------------------------------------
# C1: score fallback from last_question_context
# ---------------------------------------------------------


def test_question_node_uses_context_quality_rank_when_bundle_cleared():
    """C1: last_answer_score falls back to last_question_context.quality_rank."""
    from unittest.mock import patch
    from domain.contracts.interview_state.last_question_context import LastQuestionContext

    llm = Mock()
    llm.invoke.return_value = Mock(
        content='{"decision": "direct_question", "message": "Got it."}'
    )

    # Enable follow_up so we can verify policy receives real score
    with patch("app.graph.nodes.question_node.settings") as mock_settings:
        mock_settings.humanizer_follow_up_enabled = True
        node = build_question_node(llm)

        state = build_interview_state()
        q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
        ctx = LastQuestionContext(
            question_id="q0",
            question_prompt="Prior question",
            question_type=QuestionType.WRITTEN,
            quality_rank=4,  # OPTIMAL
        )
        state = state.model_copy(
            update={
                "questions": [q],
                "chat_history": [],
                "current_question_index": 0,
                "enable_humanizer": True,
                "last_feedback_bundle": None,  # cleared by navigation
                "last_question_context": ctx,
                "last_humanizer_follow_up": False,
                "follow_up_count": 0,
            }
        )

        new_state = node(state)

    # Policy sees score=4 (OPTIMAL) → FOLLOW_UP when enabled
    assert new_state.follow_up_count == 1
    assert new_state.last_humanizer_follow_up is True


def test_question_node_score_none_when_no_bundle_and_no_context():
    """C1: No bundle, no context → last_answer_score=None → DIRECT_QUESTION."""
    llm = Mock()
    llm.invoke.return_value = Mock(
        content='{"decision": "direct_question", "message": "Next."}'
    )

    node = build_question_node(llm)
    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "enable_humanizer": True,
            "last_feedback_bundle": None,
            "last_question_context": None,
            "follow_up_count": 0,
        }
    )

    new_state = node(state)

    assert new_state.follow_up_count == 0


# ---------------------------------------------------------
# H1: humanizer exception fallback
# ---------------------------------------------------------


def test_question_node_humanizer_exception_falls_back_to_raw_prompt():
    """H1: LLM failure → interview continues with raw question.prompt."""
    llm = Mock()
    llm.invoke.side_effect = RuntimeError("LLM unavailable")

    node = build_question_node(llm)
    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "enable_humanizer": True,
        }
    )

    new_state = node(state)

    assert new_state.question_display_text == q.prompt
    assert q.prompt in new_state.chat_history


def test_question_node_humanizer_parse_failure_does_not_abort():
    """H1: Malformed LLM JSON → fallback, graph continues."""
    llm = Mock()
    llm.invoke.return_value = Mock(content="not valid json at all")

    node = build_question_node(llm)
    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "enable_humanizer": True,
        }
    )

    new_state = node(state)

    assert new_state.question_display_text == q.prompt
