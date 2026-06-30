# tests/domain/contracts/reasoning/test_reasoning_trace.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.reasoning_trace import ReasoningTrace, ReasoningTraceStep


def _make_step(**overrides) -> ReasoningTraceStep:
    defaults = dict(
        step_id="step-1",
        component="ReasoningDepthDetector",
        rule_name="shallow_answer_check",
    )
    defaults.update(overrides)
    return ReasoningTraceStep(**defaults)


def test_step_defaults():
    step = _make_step()
    assert step.confidence_delta == 0.0
    assert step.execution_time_ms == 0.0
    assert step.summary == ""


def test_step_immutable():
    step = _make_step()
    with pytest.raises((ValidationError, TypeError)):
        step.component = "Other"


def test_step_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        _make_step(candidate_answer="user text here")


def test_step_id_non_empty():
    with pytest.raises(ValidationError):
        _make_step(step_id="")


def test_step_component_non_empty():
    with pytest.raises(ValidationError):
        _make_step(component="")


def test_step_confidence_delta_bounds():
    with pytest.raises(ValidationError):
        _make_step(confidence_delta=1.1)
    with pytest.raises(ValidationError):
        _make_step(confidence_delta=-1.1)


def test_step_summary_max_length():
    with pytest.raises(ValidationError):
        _make_step(summary="x" * 301)


def test_trace_defaults():
    trace = ReasoningTrace()
    assert trace.steps == []


def test_trace_immutable():
    trace = ReasoningTrace()
    with pytest.raises((ValidationError, TypeError)):
        trace.steps = []


def test_trace_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        ReasoningTrace(raw_output="something")


def test_trace_with_steps():
    step = _make_step()
    trace = ReasoningTrace(steps=[step])
    assert len(trace.steps) == 1
    assert trace.steps[0].step_id == "step-1"


def test_trace_serialization():
    step = _make_step(summary="shallow pattern detected")
    trace = ReasoningTrace(steps=[step])
    data = trace.model_dump()
    trace2 = ReasoningTrace(**data)
    assert trace == trace2
