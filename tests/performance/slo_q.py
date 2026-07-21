# tests/performance/slo_q.py
# EPIC-V13-09 C1 — SLO-Q written evaluation cycle harness (AR-01, AR-02, MEAS-01/04/07).

from __future__ import annotations

from unittest.mock import MagicMock

from app.graph.interview_graph import build_interview_graph
from domain.contracts.interview_state import InterviewState
from tests.factories.interview_state_factory import build_written_question_state
from tests.performance.helpers import measure_wall_clock_ms
from tests.performance.stub_llm import DeterministicStubLLM


def _coerce_state(result: object) -> InterviewState:
    if isinstance(result, InterviewState):
        return result
    if isinstance(result, dict):
        return InterviewState.model_validate(result)
    raise TypeError(f"Unexpected graph.invoke result type: {type(result)!r}")


def measure_written_cycle_ms(
    *,
    llm: DeterministicStubLLM | None = None,
) -> tuple[InterviewState, float, DeterministicStubLLM]:
    """
    Wall-clock one written evaluation ``graph.invoke`` (AR-01).

    Path under measurement: written → feedback → reasoner → decision.
    Measurement owned by harness at invoke boundary (AR-02 / MEAS-01).
    """
    stub = llm if llm is not None else DeterministicStubLLM()
    graph = build_interview_graph(llm=stub, hint_service=MagicMock())
    state = build_written_question_state()

    result, elapsed_ms = measure_wall_clock_ms(lambda: graph.invoke(state))
    return _coerce_state(result), elapsed_ms, stub
