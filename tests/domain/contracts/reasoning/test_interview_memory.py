# tests/domain/contracts/reasoning/test_interview_memory.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.coverage_state import CoverageState
from domain.contracts.reasoning.reasoning_history import ReasoningHistory
from domain.contracts.reasoning.session_metrics import SessionMetrics


def test_defaults():
    mem = InterviewMemory()
    assert isinstance(mem.evidence_store, EvidenceStore)
    assert isinstance(mem.coverage_state, CoverageState)
    assert isinstance(mem.reasoning_history, ReasoningHistory)
    assert isinstance(mem.session_metrics, SessionMetrics)
    assert mem.schema_version == "1.0"


def test_immutable():
    mem = InterviewMemory()
    with pytest.raises((ValidationError, TypeError)):
        mem.schema_version = "2.0"


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        InterviewMemory(unknown="x")


def test_four_substructures_only():
    fields = set(InterviewMemory.model_fields.keys())
    expected = {
        "evidence_store",
        "coverage_state",
        "reasoning_history",
        "session_metrics",
        "schema_version",
    }
    assert fields == expected


def test_serialization_roundtrip():
    mem = InterviewMemory()
    data = mem.model_dump()
    mem2 = InterviewMemory(**data)
    assert mem == mem2
