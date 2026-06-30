# tests/graph/nodes/test_question_node_follow_up_integration.py
#
# M1-4 runtime integration tests for M1-5D.
# All LLM calls are mocked; no network I/O.

import json
import pytest
from unittest.mock import MagicMock, patch

from app.graph.nodes.question_node import build_question_node
from tests.factories.interview_state_factory import build_interview_state, build_question
from domain.contracts.question.question import QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview_state.last_question_context import LastQuestionContext
from domain.events.follow_up_triggered_event import FollowUpTriggeredEvent
from domain.events.follow_up_skipped_event import FollowUpSkippedEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AREA = "technical_knowledge"

_VALID_LLM_JSON = json.dumps({
    "follow_up_question": (
        "How does LRU eviction affect technical knowledge performance "
        "under high memory pressure?"
    ),
    "reasoning": "Candidate mentioned LRU but did not address memory limits.",
    "topic_anchor": "LRU eviction",
    "confidence": 0.85,
})

_VALID_HUMANIZER_JSON = json.dumps({
    "decision": "direct_question",
    "message": "Can you explain caching in detail?",
    "score": 6,
    "follow_up_used": False,
})


def _make_llm(response_text: str) -> MagicMock:
    llm = MagicMock()
    msg = MagicMock()
    msg.content = response_text
    llm.invoke.return_value = msg
    return llm


def _written_question(qid: str = "q1", supports_follow_up: bool = True):
    return build_question(qid=qid, qtype=QuestionType.WRITTEN).model_copy(
        update={
            "area": InterviewArea.TECH_CODING,
            "prompt": "Explain Redis caching eviction.",
            "supports_follow_up": supports_follow_up,
        }
    )


def _state_with_follow_up_slot(
    question,
    *,
    previous_answer: str = "I used LRU for Redis caching technical knowledge.",
    follow_up_count: int = 0,
):
    """Build a state where index 0 is in follow_up_eligible_indices."""
    from domain.contracts.interview_state import InterviewState
    from domain.contracts.interview.answer import Answer
    from domain.contracts.user.role import Role, RoleType
    from domain.contracts.interview.interview_type import InterviewType

    ctx = LastQuestionContext(
        question_id="q0",
        question_prompt="Explain Redis caching.",
        question_type=QuestionType.WRITTEN,
        question_area=_AREA,
        answer_content=previous_answer,
        quality_rank=4,
    )

    return InterviewState(
        interview_id="test-id",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="TestCorp",
        interview_type=InterviewType.TECHNICAL,
        language="en",
        questions=[question],
        answers=[],
        current_question_index=0,
        follow_up_eligible_indices=frozenset({0}),
        last_question_context=ctx,
        follow_up_count=follow_up_count,
    )


# ---------------------------------------------------------------------------
# INT-001: happy path — follow-up accepted
# ---------------------------------------------------------------------------

def test_int_001_follow_up_accepted_updates_state() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    llm = _make_llm(_VALID_LLM_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    assert new_state.follow_up_count == 1
    assert new_state.last_humanizer_follow_up is True
    assert "LRU eviction" in new_state.question_display_text
    assert len(new_state.events) == 1
    assert isinstance(new_state.events[0], FollowUpTriggeredEvent)


# ---------------------------------------------------------------------------
# INT-002: supports_follow_up=False skips V1.1 pipeline
# ---------------------------------------------------------------------------

def test_int_002_supports_follow_up_false_skips() -> None:
    """supports_follow_up=False must skip the V1.1 pipeline (no FollowUpTriggeredEvent
    from the new engine). The V1.0 humanizer path may still produce output."""
    question = _written_question(supports_follow_up=False)
    state = _state_with_follow_up_slot(question)
    # LLM for V1.0 fallback
    llm = _make_llm(_VALID_HUMANIZER_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    # V1.1 pipeline must NOT have been invoked
    assert not any(isinstance(e, FollowUpTriggeredEvent) for e in new_state.events)
    # V1.1 follow-up pipeline produced no skip event either
    assert not any(isinstance(e, FollowUpSkippedEvent) for e in new_state.events)


# ---------------------------------------------------------------------------
# INT-003: index NOT in eligible_indices → V1.0 path (no V1.1 events)
# ---------------------------------------------------------------------------

def test_int_003_not_in_eligible_indices_uses_v10_path() -> None:
    """When index is not in eligible set, V1.1 pipeline is not invoked."""
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    # Remove index 0 from eligible
    state = state.model_copy(update={"follow_up_eligible_indices": frozenset()})
    llm = _make_llm(_VALID_HUMANIZER_JSON)

    node = build_question_node(llm)
    new_state = node(state)

    # No V1.1 events
    assert not any(isinstance(e, FollowUpTriggeredEvent) for e in new_state.events)
    assert not any(isinstance(e, FollowUpSkippedEvent) for e in new_state.events)


# ---------------------------------------------------------------------------
# INT-004: guard rejects → FollowUpSkippedEvent + fallback to V1.0
# ---------------------------------------------------------------------------

def test_int_004_guard_rejected_emits_skip_event() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    # JSON that passes strict parse and DTO but guard rejects:
    # follow_up_question ends with ? (DTO ok) but has no area token and no keyword overlap
    bad_follow_up = json.dumps({
        "follow_up_question": "Tell me about your hobby hiking trips?",
        "reasoning": "test",
        "topic_anchor": "hobbies",
        "confidence": 0.5,
    })
    # First call = follow-up attempt (fails guard), second = V1.0 humanizer
    call_count = [0]
    def fake_invoke(prompt):
        msg = MagicMock()
        if call_count[0] == 0:
            msg.content = bad_follow_up
        else:
            msg.content = _VALID_HUMANIZER_JSON
        call_count[0] += 1
        return msg

    llm = MagicMock()
    llm.invoke.side_effect = fake_invoke

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    # V1.1 pipeline must have emitted a SkippedEvent
    skip_events = [e for e in new_state.events if isinstance(e, FollowUpSkippedEvent)]
    assert len(skip_events) == 1
    assert skip_events[0].reason == "guard_rejected"
    # V1.1 follow-up must NOT have been accepted
    assert not any(isinstance(e, FollowUpTriggeredEvent) for e in new_state.events)


# ---------------------------------------------------------------------------
# INT-005: parse error → FollowUpSkippedEvent + fallback to V1.0
# ---------------------------------------------------------------------------

def test_int_005_parse_error_emits_skip_event() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    call_count = [0]

    def fake_invoke(prompt):
        msg = MagicMock()
        if call_count[0] == 0:
            msg.content = "not valid json at all"
        else:
            msg.content = _VALID_HUMANIZER_JSON
        call_count[0] += 1
        return msg

    llm = MagicMock()
    llm.invoke.side_effect = fake_invoke

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    skip_events = [e for e in new_state.events if isinstance(e, FollowUpSkippedEvent)]
    assert len(skip_events) == 1
    assert skip_events[0].reason == "parse_error"
    assert not any(isinstance(e, FollowUpTriggeredEvent) for e in new_state.events)


# ---------------------------------------------------------------------------
# INT-006: no_context (no last_question_context) → FollowUpSkippedEvent
# ---------------------------------------------------------------------------

def test_int_006_no_context_emits_skip_event() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    # Remove context
    state = state.model_copy(update={"last_question_context": None})
    llm = _make_llm(_VALID_HUMANIZER_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    skip_events = [e for e in new_state.events if isinstance(e, FollowUpSkippedEvent)]
    assert len(skip_events) == 1
    assert skip_events[0].reason == "no_context"


# ---------------------------------------------------------------------------
# INT-007: follow_up_count incremented on acceptance
# ---------------------------------------------------------------------------

def test_int_007_follow_up_count_incremented() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question, follow_up_count=0)
    llm = _make_llm(_VALID_LLM_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    assert new_state.follow_up_count == 1


# ---------------------------------------------------------------------------
# INT-008: humanizer_follow_up_enabled=False → never triggers follow-up
# ---------------------------------------------------------------------------

def test_int_008_follow_up_disabled_globally() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    llm = _make_llm(_VALID_HUMANIZER_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", False):
        node = build_question_node(llm)
        new_state = node(state)

    assert new_state.follow_up_count == 0
    assert not any(isinstance(e, FollowUpTriggeredEvent) for e in new_state.events)


# ---------------------------------------------------------------------------
# INT-009: FollowUpTriggeredEvent fields correct
# ---------------------------------------------------------------------------

def test_int_009_triggered_event_fields() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    llm = _make_llm(_VALID_LLM_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    event = new_state.events[0]
    assert isinstance(event, FollowUpTriggeredEvent)
    assert event.question_index == 0
    assert event.question_area == _AREA
    assert event.follow_up_count == 1
    assert 0.0 <= event.guard_score <= 1.0
    assert event.latency_ms >= 0


# ---------------------------------------------------------------------------
# INT-010: FollowUpSkippedEvent fields correct
# ---------------------------------------------------------------------------

def test_int_010_skipped_event_fields() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    state = state.model_copy(update={"last_question_context": None})
    llm = _make_llm(_VALID_HUMANIZER_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    event = next(e for e in new_state.events if isinstance(e, FollowUpSkippedEvent))
    assert event.question_index == 0
    assert event.reason == "no_context"
    assert event.latency_ms >= 0


# ---------------------------------------------------------------------------
# INT-011: empty eligible indices → no follow-up attempt
# ---------------------------------------------------------------------------

def test_int_011_empty_eligible_indices_no_follow_up() -> None:
    question = _written_question()
    # eligible_indices defaults to frozenset() in factory
    state = build_interview_state(questions=[question])
    state = state.model_copy(update={"questions": [question], "current_question_index": 0})
    llm = _make_llm(_VALID_HUMANIZER_JSON)

    node = build_question_node(llm)
    new_state = node(state)

    assert not any(isinstance(e, FollowUpTriggeredEvent) for e in new_state.events)


# ---------------------------------------------------------------------------
# INT-012: interview never interrupted by follow-up failure
# ---------------------------------------------------------------------------

def test_int_012_interview_never_interrupted() -> None:
    """Follow-up generation failure must never raise to the caller."""
    question = _written_question()
    state = _state_with_follow_up_slot(question)

    llm = MagicMock()
    llm.invoke.side_effect = RuntimeError("LLM exploded")

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        # Should not raise
        new_state = node(state)

    assert new_state is not None
    # question_display_text falls back to raw prompt
    assert new_state.question_display_text is not None


# ---------------------------------------------------------------------------
# INT-013: non-WRITTEN question never triggers follow-up
# ---------------------------------------------------------------------------

def test_int_013_coding_question_no_follow_up() -> None:
    question = build_question(qid="q1", qtype=QuestionType.CODING).model_copy(
        update={"supports_follow_up": True}
    )
    state = _state_with_follow_up_slot(question)
    llm = _make_llm(_VALID_HUMANIZER_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    assert not any(isinstance(e, FollowUpTriggeredEvent) for e in new_state.events)


# ---------------------------------------------------------------------------
# INT-014: last_humanizer_follow_up=True on acceptance
# ---------------------------------------------------------------------------

def test_int_014_last_humanizer_follow_up_flag() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    llm = _make_llm(_VALID_LLM_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    assert new_state.last_humanizer_follow_up is True


# ---------------------------------------------------------------------------
# INT-015: events list grows monotonically
# ---------------------------------------------------------------------------

def test_int_015_events_appended_not_replaced() -> None:
    question = _written_question()
    state = _state_with_follow_up_slot(question)
    # Pre-populate with an existing event
    from domain.events.answer_submitted_event import AnswerSubmittedEvent
    existing = AnswerSubmittedEvent(question_id="q0", content="some answer")
    state = state.model_copy(update={"events": [existing]})
    llm = _make_llm(_VALID_LLM_JSON)

    with patch("infrastructure.config.settings.settings.humanizer_follow_up_enabled", True):
        node = build_question_node(llm)
        new_state = node(state)

    assert len(new_state.events) == 2
    assert new_state.events[0] is existing


# ---------------------------------------------------------------------------
# Regression: existing V1.0 paths still work
# ---------------------------------------------------------------------------

def test_reg_humanizer_disabled_still_works() -> None:
    q = _written_question()
    state = build_interview_state(questions=[q])
    state = state.model_copy(update={"enable_humanizer": False})
    llm = MagicMock()
    node = build_question_node(llm)
    new_state = node(state)
    assert q.prompt in new_state.chat_history
    llm.invoke.assert_not_called()


def test_reg_prevent_double_processing_unchanged() -> None:
    q = _written_question()
    state = build_interview_state(questions=[q])
    state = state.model_copy(
        update={
            "chat_history": ["already here"],
            "current_question_index": 0,
        }
    )
    llm = MagicMock()
    node = build_question_node(llm)
    new_state = node(state)
    llm.invoke.assert_not_called()
    assert new_state.chat_history == state.chat_history
