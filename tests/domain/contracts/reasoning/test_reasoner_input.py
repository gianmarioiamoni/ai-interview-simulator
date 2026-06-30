# tests/domain/contracts/reasoning/test_reasoner_input.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.interview_memory import InterviewMemory


def _make_input(**overrides) -> ReasonerInput:
    defaults = dict(session_id="sess-1", question_index=2)
    defaults.update(overrides)
    return ReasonerInput(**defaults)


def test_defaults():
    inp = _make_input()
    assert isinstance(inp.interview_memory, InterviewMemory)
    assert inp.role == ""
    assert inp.seniority == "mid"
    assert inp.interview_type == "technical"
    assert inp.max_follow_ups == 2
    assert inp.follow_up_count == 0
    assert inp.questions_remaining == 0
    assert inp.follow_up_eligible_indices == frozenset()


def test_immutable():
    inp = _make_input()
    with pytest.raises((ValidationError, TypeError)):
        inp.session_id = "other"


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        _make_input(extra_field="x")


def test_session_id_non_empty():
    with pytest.raises(ValidationError):
        _make_input(session_id="")


def test_question_index_non_negative():
    with pytest.raises(ValidationError):
        _make_input(question_index=-1)


def test_evaluation_score_bounds():
    with pytest.raises(ValidationError):
        _make_input(current_evaluation_score=101.0)
    with pytest.raises(ValidationError):
        _make_input(current_evaluation_score=-1.0)


def test_none_answer_allowed():
    inp = _make_input(current_answer_content=None)
    assert inp.current_answer_content is None


def test_frozenset_eligible_indices():
    inp = _make_input(follow_up_eligible_indices=frozenset({1, 3, 5}))
    assert 3 in inp.follow_up_eligible_indices
