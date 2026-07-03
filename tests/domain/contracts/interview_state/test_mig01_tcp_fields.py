# tests/domain/contracts/interview_state/test_mig01_tcp_fields.py
# MIG-01 — TCP field tests (RIB-01, PAT-04)
#
# Verifies:
# 1. TCP fields present and default to None.
# 2. InterviewState remains backward-compatible (all V1.1 tests pass).
# 3. No LangGraph node references the new fields (architectural).
# 4. extra=forbid preserved.
# 5. arbitrary_types_allowed added correctly.
# 6. Correct contract types used (no duplicates).

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_state.base import InterviewStateBase
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.session_history.session_history import SessionHistory
from domain.contracts.user.role import Role, RoleType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_kwargs() -> dict:
    return {
        "interview_id": "mig01-test",
        "role": Role(type=RoleType.BACKEND_ENGINEER),
        "company": "ACME",
    }


def _make_state(**overrides) -> InterviewState:
    return InterviewState(**{**_base_kwargs(), **overrides})


# ---------------------------------------------------------------------------
# TCP field presence and defaults
# ---------------------------------------------------------------------------

class TestTCPFieldsPresence:
    def test_observation_store_defaults_to_none(self) -> None:
        state = _make_state()
        assert state.observation_store is None

    def test_candidate_profile_v2_defaults_to_none(self) -> None:
        state = _make_state()
        assert state.candidate_profile_v2 is None

    def test_session_history_defaults_to_none(self) -> None:
        state = _make_state()
        assert state.session_history is None

    def test_all_three_tcp_fields_exist_on_base(self) -> None:
        fields = InterviewStateBase.model_fields
        assert "observation_store" in fields
        assert "candidate_profile_v2" in fields
        assert "session_history" in fields

    def test_tcp_fields_are_optional(self) -> None:
        fields = InterviewStateBase.model_fields
        for name in ("observation_store", "candidate_profile_v2", "session_history"):
            assert fields[name].is_required() is False, f"{name} must not be required"

    def test_tcp_field_descriptions_contain_v12_marker(self) -> None:
        fields = InterviewStateBase.model_fields
        for name in ("observation_store", "candidate_profile_v2", "session_history"):
            desc = fields[name].description or ""
            assert "V1.2 TCP" in desc, f"{name} description must contain 'V1.2 TCP'"


# ---------------------------------------------------------------------------
# model_config validation
# ---------------------------------------------------------------------------

class TestModelConfig:
    def test_extra_forbid_preserved(self) -> None:
        assert InterviewStateBase.model_config.get("extra") == "forbid"

    def test_arbitrary_types_allowed(self) -> None:
        assert InterviewStateBase.model_config.get("arbitrary_types_allowed") is True

    def test_extra_field_still_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InterviewState(**_base_kwargs(), _unknown_field="value")


# ---------------------------------------------------------------------------
# Backward compatibility — V1.1 fields still exist and behave correctly
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_interview_memory_still_present(self) -> None:
        from domain.contracts.reasoning.interview_memory import InterviewMemory
        state = _make_state()
        assert isinstance(state.interview_memory, InterviewMemory)

    def test_current_reasoning_decision_still_none_by_default(self) -> None:
        state = _make_state()
        assert state.current_reasoning_decision is None

    def test_follow_up_count_still_validated(self) -> None:
        with pytest.raises(ValidationError):
            _make_state(follow_up_count=99)

    def test_v11_state_serialises_with_tcp_as_none(self) -> None:
        state = _make_state()
        d = state.model_dump()
        assert d["observation_store"] is None
        assert d["candidate_profile_v2"] is None
        assert d["session_history"] is None

    def test_model_copy_preserves_tcp_defaults(self) -> None:
        state = _make_state()
        new_state = state.model_copy(update={"follow_up_count": 1})
        assert new_state.observation_store is None
        assert new_state.candidate_profile_v2 is None
        assert new_state.session_history is None


# ---------------------------------------------------------------------------
# Contract uniqueness — correct types, no duplicates
# ---------------------------------------------------------------------------

class TestContractUniqueness:
    def test_candidate_profile_v2_type_is_v11_candidate_profile(self) -> None:
        """candidate_profile_v2 uses the single CandidateProfile contract (domain/contracts/reasoning)."""
        annotation = InterviewStateBase.model_fields["candidate_profile_v2"].annotation
        # Optional[CandidateProfile] — unwrap Union
        import typing
        args = typing.get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        assert len(non_none) == 1
        assert non_none[0] is CandidateProfile

    def test_observation_store_type_is_abc(self) -> None:
        annotation = InterviewStateBase.model_fields["observation_store"].annotation
        import typing
        args = typing.get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        assert len(non_none) == 1
        assert non_none[0] is ObservationStore

    def test_session_history_type_is_correct_contract(self) -> None:
        annotation = InterviewStateBase.model_fields["session_history"].annotation
        import typing
        args = typing.get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        assert len(non_none) == 1
        assert non_none[0] is SessionHistory

    def test_single_candidate_profile_class_in_domain(self) -> None:
        """Architectural: exactly one class named CandidateProfile in domain/contracts."""
        domain_contracts = Path("domain/contracts")
        matches = []
        for py_file in domain_contracts.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "CandidateProfile":
                    matches.append(str(py_file))
        assert matches == ["domain/contracts/reasoning/candidate_profile.py"], (
            f"Expected exactly one CandidateProfile in domain/contracts/reasoning. Found: {matches}"
        )

    def test_single_session_history_class_in_domain(self) -> None:
        domain_contracts = Path("domain/contracts")
        matches = []
        for py_file in domain_contracts.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "SessionHistory":
                    matches.append(str(py_file))
        assert matches == ["domain/contracts/session_history/session_history.py"], (
            f"Expected exactly one SessionHistory. Found: {matches}"
        )

    def test_single_knowledge_snapshot_class_in_domain(self) -> None:
        domain_contracts = Path("domain/contracts")
        matches = []
        for py_file in domain_contracts.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "KnowledgeSnapshot":
                    matches.append(str(py_file))
        assert matches == ["domain/contracts/knowledge_snapshot/knowledge_snapshot.py"], (
            f"Expected exactly one KnowledgeSnapshot. Found: {matches}"
        )


# ---------------------------------------------------------------------------
# Architectural: no LangGraph node reads TCP fields
# ---------------------------------------------------------------------------

class TestNoNodeReadsNewFields:
    """Architectural guard: V1.1 nodes must not reference the TCP fields."""

    _NODES_DIR = Path("app/graph/nodes")
    _TCP_FIELD_NAMES = {"observation_store", "candidate_profile_v2", "session_history"}

    def _nodes_referencing(self, field: str) -> list[str]:
        offenders = []
        for py_file in self._NODES_DIR.glob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            source = py_file.read_text()
            if field in source:
                offenders.append(py_file.name)
        return offenders

    def test_no_node_reads_observation_store(self) -> None:
        # MIG-02: reasoner_node (writer); MIG-04: session_close_node (reader).
        permitted = {"reasoner_node.py", "session_close_node.py"}
        offenders = set(self._nodes_referencing("observation_store")) - permitted
        assert offenders == set(), (
            f"Unexpected graph node(s) reference observation_store: {offenders}"
        )

    def test_no_node_reads_candidate_profile_v2(self) -> None:
        # MIG-03: reasoner_node (writer); MIG-04: session_close_node (reader).
        permitted = {"reasoner_node.py", "session_close_node.py"}
        offenders = set(self._nodes_referencing("candidate_profile_v2")) - permitted
        assert offenders == set(), (
            f"Unexpected graph node(s) reference candidate_profile_v2: {offenders}"
        )

    def test_no_node_reads_session_history(self) -> None:
        # MIG-04: session_close_node is the sole writer of session_history.
        permitted = {"session_close_node.py"}
        offenders = set(self._nodes_referencing("session_history")) - permitted
        assert offenders == set(), (
            f"Unexpected graph node(s) reference session_history: {offenders}"
        )
