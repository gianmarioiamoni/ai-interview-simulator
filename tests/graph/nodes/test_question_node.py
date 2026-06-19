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


def test_question_node_database_schema_displayed():
    """DATABASE questions prepend schema block before the prompt."""
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
    assert "**Database Schema**" in history_entry
    assert "CREATE TABLE employees" in history_entry
    assert q.prompt in history_entry
    assert history_entry.index("Database Schema") < history_entry.index(q.prompt)


def test_question_node_database_no_schema_unchanged():
    """DATABASE question without db_schema shows prompt only."""
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


def test_question_node_coding_no_schema_injected():
    """CODING questions are never modified with schema blocks."""
    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.CODING})
    state = state.model_copy(update={"questions": [q]})

    new_state = node(state)

    assert new_state.chat_history[-1] == q.prompt
    assert "Database Schema" not in new_state.chat_history[-1]


def test_question_node_database_schema_humanizer_disabled():
    """Schema is injected even when humanizer is disabled."""
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
    assert "**Database Schema**" in history_entry
    assert "CREATE TABLE orders" in history_entry


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
