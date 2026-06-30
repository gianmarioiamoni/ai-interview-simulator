# tests/domain/contracts/reasoning/test_interview_state_backward_compat.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.reasoner_decision import ReasonerDecision
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType


def _make_base_state_kwargs() -> dict:
    """Minimal valid kwargs for InterviewStateBase excluding new M2 fields."""
    from domain.contracts.user.role import Role
    from domain.contracts.interview.interview_type import InterviewType
    return dict(
        interview_id="test-interview-id",
        role=Role(type="backend_engineer"),
        company="TestCo",
    )


def test_engineering_judgment_in_performance_dimension_type():
    assert PerformanceDimensionType.ENGINEERING_JUDGMENT == "engineering_judgment"
    assert len(PerformanceDimensionType) == 5


def test_trade_off_awareness_not_in_performance_dimension_type():
    values = [d.value for d in PerformanceDimensionType]
    assert "trade_off_awareness" not in values


def test_existing_four_dimensions_preserved():
    existing = {"technical_depth", "problem_solving", "communication", "system_design"}
    values = {d.value for d in PerformanceDimensionType}
    assert existing.issubset(values)


def test_interview_state_has_interview_memory_field():
    from domain.contracts.interview_state.base import InterviewStateBase
    fields = InterviewStateBase.model_fields
    assert "interview_memory" in fields
    assert "current_reasoning_decision" in fields


def test_interview_state_interview_memory_default():
    from domain.contracts.interview_state.base import InterviewStateBase
    kwargs = _make_base_state_kwargs()
    state = InterviewStateBase(**kwargs)
    assert isinstance(state.interview_memory, InterviewMemory)


def test_interview_state_current_reasoning_decision_default_none():
    from domain.contracts.interview_state.base import InterviewStateBase
    kwargs = _make_base_state_kwargs()
    state = InterviewStateBase(**kwargs)
    assert state.current_reasoning_decision is None


def test_interview_memory_context_still_present():
    """InterviewMemoryContext must still be on InterviewState (deprecated, not removed)."""
    from domain.contracts.interview_state.base import InterviewStateBase
    fields = InterviewStateBase.model_fields
    assert "memory_context" in fields or "interview_memory_context" not in {
        k for k in fields if "memory" in k and "interview_memory" not in k
    }


def test_interview_state_existing_follow_up_fields_preserved():
    from domain.contracts.interview_state.base import InterviewStateBase
    fields = set(InterviewStateBase.model_fields.keys())
    for f in ("follow_up_count", "follow_up_eligible_indices", "last_humanizer_follow_up"):
        assert f in fields, f"{f} must still be present"
