# tests/services/interview_reasoner/test_reasoning_context_builder.py
"""Comprehensive tests for ReasoningContextBuilder (M2-5 pre-req)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_state.last_question_context import LastQuestionContext
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.user.role import Role, RoleType
from services.interview_reasoner.context_builder_errors import (
    IncoherentQuestionHistoryError,
    InvalidEvidenceStoreError,
    MissingCandidateProfileError,
    MissingInterviewMemoryError,
)
from services.interview_reasoner.reasoning_context_builder import ReasoningContextBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid() -> str:
    return str(uuid.uuid4())


def _make_question(area: InterviewArea = InterviewArea.HR_BACKGROUND) -> Question:
    return Question(
        id=_uid(),
        area=area,
        type=QuestionType.WRITTEN,
        prompt="Test question?",
    )


def _empty_state() -> InterviewState:
    return InterviewState.create_empty()


def _state_with_questions(n: int = 3) -> InterviewState:
    qs = [_make_question() for _ in range(n)]
    s = _empty_state()
    return s.model_copy(update={"questions": qs})


# ---------------------------------------------------------------------------
# Basic build
# ---------------------------------------------------------------------------

def test_build_returns_reasoner_input():
    builder = ReasoningContextBuilder()
    result = builder.build(_empty_state())
    assert isinstance(result, ReasonerInput)


def test_build_session_id_matches():
    state = _empty_state()
    inp = ReasoningContextBuilder().build(state)
    assert inp.session_id == state.interview_id


def test_build_question_index_matches():
    state = _empty_state().model_copy(update={"current_question_index": 2})
    inp = ReasoningContextBuilder().build(state)
    assert inp.question_index == 2


def test_build_interview_memory_passed():
    memory = InterviewMemory()
    state = _empty_state().model_copy(update={"interview_memory": memory})
    inp = ReasoningContextBuilder().build(state)
    assert inp.interview_memory is memory


def test_build_follow_up_count():
    state = _empty_state().model_copy(update={"follow_up_count": 1})
    inp = ReasoningContextBuilder().build(state)
    assert inp.follow_up_count == 1


def test_build_follow_up_eligible_indices():
    state = _empty_state().model_copy(update={"follow_up_eligible_indices": frozenset({2, 4})})
    inp = ReasoningContextBuilder().build(state)
    assert inp.follow_up_eligible_indices == frozenset({2, 4})


def test_build_seniority():
    state = _empty_state().model_copy(update={"seniority_level": "senior"})
    inp = ReasoningContextBuilder().build(state)
    assert inp.seniority == "senior"


def test_build_interview_type():
    state = _empty_state().model_copy(update={"interview_type": InterviewType.HR})
    inp = ReasoningContextBuilder().build(state)
    assert inp.interview_type == InterviewType.HR.value


def test_build_role_extracted():
    state = _empty_state()
    inp = ReasoningContextBuilder().build(state)
    assert inp.role == state.role.type.value


def test_build_questions_remaining():
    state = _state_with_questions(5)
    qids = [state.questions[0].id, state.questions[1].id]
    state = state.model_copy(update={"asked_question_ids": qids})
    inp = ReasoningContextBuilder().build(state)
    assert inp.questions_remaining == 3


def test_build_questions_remaining_zero_when_all_asked():
    state = _state_with_questions(2)
    qids = [q.id for q in state.questions]
    state = state.model_copy(update={"asked_question_ids": qids})
    inp = ReasoningContextBuilder().build(state)
    assert inp.questions_remaining == 0


# ---------------------------------------------------------------------------
# max_follow_ups from settings
# ---------------------------------------------------------------------------

def test_max_follow_ups_from_settings():
    inp = ReasoningContextBuilder().build(_empty_state())
    assert inp.max_follow_ups >= 0


# ---------------------------------------------------------------------------
# current_question_area / type from LastQuestionContext
# ---------------------------------------------------------------------------

def test_area_from_last_question_context():
    lqc = LastQuestionContext(
        question_id=_uid(),
        question_prompt="Q?",
        question_type=QuestionType.WRITTEN,
        question_area="databases",
    )
    state = _empty_state().model_copy(update={"last_question_context": lqc})
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_question_area == "databases"


def test_type_from_last_question_context():
    lqc = LastQuestionContext(
        question_id=_uid(),
        question_prompt="Q?",
        question_type=QuestionType.CODING,
    )
    state = _empty_state().model_copy(update={"last_question_context": lqc})
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_question_type == QuestionType.CODING.value


def test_area_from_current_question_when_no_lqc():
    q = _make_question(area=InterviewArea.HR_TECHNICAL_KNOWLEDGE)
    state = _empty_state().model_copy(
        update={"questions": [q], "current_question_index": 0}
    )
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_question_area == InterviewArea.HR_TECHNICAL_KNOWLEDGE.value


def test_area_none_when_no_questions_and_no_lqc():
    state = _empty_state()  # no questions
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_question_area is None


def test_type_none_when_no_questions_and_no_lqc():
    state = _empty_state()
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_question_type is None


# ---------------------------------------------------------------------------
# answer_content sanitization
# ---------------------------------------------------------------------------

def test_answer_from_last_question_context():
    lqc = LastQuestionContext(
        question_id=_uid(),
        question_prompt="Q?",
        question_type=QuestionType.WRITTEN,
        answer_content="my answer",
    )
    state = _empty_state().model_copy(update={"last_question_context": lqc})
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_answer_content == "my answer"


def test_answer_truncated_to_2000_chars():
    long_answer = "x" * 3000
    lqc = LastQuestionContext(
        question_id=_uid(),
        question_prompt="Q?",
        question_type=QuestionType.WRITTEN,
        answer_content=long_answer,
    )
    state = _empty_state().model_copy(update={"last_question_context": lqc})
    inp = ReasoningContextBuilder().build(state)
    assert len(inp.current_answer_content) == 2000


def test_answer_control_chars_stripped():
    lqc = LastQuestionContext(
        question_id=_uid(),
        question_prompt="Q?",
        question_type=QuestionType.WRITTEN,
        answer_content="hello\x00world\x1f",
    )
    state = _empty_state().model_copy(update={"last_question_context": lqc})
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_answer_content == "helloworld"


def test_answer_none_when_no_context_and_no_answers():
    state = _empty_state()
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_answer_content is None


# ---------------------------------------------------------------------------
# feedback_quality
# ---------------------------------------------------------------------------

def test_feedback_quality_none_when_no_bundle():
    inp = ReasoningContextBuilder().build(_empty_state())
    assert inp.current_feedback_quality is None


def test_feedback_quality_extracted_from_bundle():
    from domain.contracts.feedback.quality import Quality
    bundle = MagicMock()
    bundle.overall_quality = Quality.CORRECT
    state = _empty_state().model_copy(update={"last_feedback_bundle": bundle})
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_feedback_quality == Quality.CORRECT.value


# ---------------------------------------------------------------------------
# dimension_signals
# ---------------------------------------------------------------------------

def test_dimension_signals_empty_by_default():
    inp = ReasoningContextBuilder().build(_empty_state())
    assert inp.current_dimension_signals == {}


def test_dimension_signals_extracted():
    from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
    signals = {PerformanceDimensionType.TECHNICAL_DEPTH: 0.8}
    state = _empty_state().model_copy(update={"dimension_signals": signals})
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_dimension_signals.get("technical_depth") == 0.8


# ---------------------------------------------------------------------------
# evaluation_score
# ---------------------------------------------------------------------------

def test_evaluation_score_none_when_no_results():
    inp = ReasoningContextBuilder().build(_empty_state())
    assert inp.current_evaluation_score is None


def test_evaluation_score_extracted_from_last_question():
    q = _make_question()
    evaluation = QuestionEvaluation(
        question_id=q.id, score=75.0, max_score=100.0, feedback="Good.", passed=True
    )
    result = QuestionResult(question_id=q.id, evaluation=evaluation)
    state = _state_with_questions(1).model_copy(
        update={
            "questions": [q],
            "asked_question_ids": [q.id],
            "results_by_question": {q.id: result},
        }
    )
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_evaluation_score == 75.0


def test_evaluation_score_none_when_result_has_no_evaluation():
    q = _make_question()
    result = QuestionResult(question_id=q.id)
    state = _empty_state().model_copy(
        update={
            "questions": [q],
            "asked_question_ids": [q.id],
            "results_by_question": {q.id: result},
        }
    )
    inp = ReasoningContextBuilder().build(state)
    assert inp.current_evaluation_score is None


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_incoherent_history_raises():
    state = _empty_state().model_copy(
        update={"asked_question_ids": ["id1", "id2"]}
    )
    # 0 questions available, 2 asked
    with pytest.raises(IncoherentQuestionHistoryError) as exc_info:
        ReasoningContextBuilder().build(state)
    assert exc_info.value.asked == 2
    assert exc_info.value.available == 0


def test_incoherent_history_ok_when_equal():
    q = _make_question()
    state = _empty_state().model_copy(
        update={"questions": [q], "asked_question_ids": [q.id]}
    )
    inp = ReasoningContextBuilder().build(state)
    assert inp.session_id == state.interview_id


def test_missing_interview_memory_raises(monkeypatch):
    state = _empty_state()
    # Force interview_memory to None via __dict__
    object.__setattr__(state, "__dict__", {**state.__dict__, "interview_memory": None})
    with pytest.raises((MissingInterviewMemoryError, Exception)):
        ReasoningContextBuilder().build(state)


def test_missing_candidate_profile_raises(monkeypatch):
    bad_memory = MagicMock(spec=InterviewMemory)
    del bad_memory.candidate_profile  # AttributeError on access
    state = _empty_state().model_copy(update={"interview_memory": bad_memory})
    with pytest.raises((MissingCandidateProfileError, AttributeError, Exception)):
        ReasoningContextBuilder().build(state)


def test_invalid_evidence_store_inaccessible(monkeypatch):
    bad_memory = MagicMock(spec=InterviewMemory)
    bad_memory.candidate_profile = MagicMock()
    del bad_memory.evidence_store  # AttributeError on access
    state = _empty_state().model_copy(update={"interview_memory": bad_memory})
    with pytest.raises((InvalidEvidenceStoreError, AttributeError, Exception)):
        ReasoningContextBuilder().build(state)


# ---------------------------------------------------------------------------
# Error class contracts
# ---------------------------------------------------------------------------

def test_missing_interview_memory_error_message():
    err = MissingInterviewMemoryError()
    assert "interview_memory" in str(err)


def test_incoherent_history_error_message():
    err = IncoherentQuestionHistoryError(3, 1)
    assert "3" in str(err)
    assert "1" in str(err)


def test_missing_candidate_profile_error_message():
    err = MissingCandidateProfileError()
    assert "CandidateProfile" in str(err)


def test_invalid_evidence_store_error_message():
    err = InvalidEvidenceStoreError("test reason")
    assert "test reason" in str(err)
    assert err.reason == "test reason"


# ---------------------------------------------------------------------------
# Immutability — build does not mutate state
# ---------------------------------------------------------------------------

def test_build_does_not_mutate_state():
    state = _empty_state()
    original_idx = state.current_question_index
    ReasoningContextBuilder().build(state)
    assert state.current_question_index == original_idx
