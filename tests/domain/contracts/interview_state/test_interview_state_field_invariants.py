# tests/domain/contracts/interview_state/test_interview_state_field_invariants.py
# Architectural invariants for InterviewState field contracts (PAT-04)
#
# Verifies:
# 1. V1.2 fields are present, optional, and correctly typed.
# 2. Model configuration: extra=forbid, arbitrary_types_allowed.
# 3. Core V1.1 fields remain present and correctly behave.
# 4. Domain contract uniqueness: one class per concept.
# 5. Sole-writer ownership: only declared nodes read/write each field.

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
        "interview_id": "field-invariants-test",
        "role": Role(type=RoleType.BACKEND_ENGINEER),
        "company": "ACME",
    }


def _make_state(**overrides) -> InterviewState:
    return InterviewState(**{**_base_kwargs(), **overrides})


# ---------------------------------------------------------------------------
# V1.2 field presence and defaults
# ---------------------------------------------------------------------------

class TestV12FieldPresence:
    def test_observation_store_defaults_to_none(self) -> None:
        state = _make_state()
        assert state.observation_store is None

    def test_candidate_profile_v2_defaults_to_none(self) -> None:
        state = _make_state()
        assert state.candidate_profile_v2 is None

    def test_session_history_defaults_to_none(self) -> None:
        state = _make_state()
        assert state.session_history is None

    def test_report_defaults_to_none(self) -> None:
        state = _make_state()
        assert state.report is None

    def test_v12_fields_exist_on_base(self) -> None:
        fields = InterviewStateBase.model_fields
        assert "observation_store" in fields
        assert "candidate_profile_v2" in fields
        assert "session_history" in fields
        assert "report" in fields

    def test_v12_fields_are_optional(self) -> None:
        fields = InterviewStateBase.model_fields
        for name in ("observation_store", "candidate_profile_v2", "session_history", "report"):
            assert fields[name].is_required() is False, f"{name} must not be required"

    def test_v12_fields_have_non_empty_descriptions(self) -> None:
        fields = InterviewStateBase.model_fields
        for name in ("observation_store", "candidate_profile_v2", "session_history", "report"):
            desc = fields[name].description or ""
            assert len(desc) > 0, f"{name} must have a non-empty field description"


# ---------------------------------------------------------------------------
# Model configuration
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
# Core field stability
# ---------------------------------------------------------------------------

class TestCoreFieldStability:
    def test_interview_memory_still_present(self) -> None:
        from domain.contracts.reasoning.interview_memory import InterviewMemory
        state = _make_state()
        assert isinstance(state.interview_memory, InterviewMemory)

    def test_deleted_ephemeral_fields_absent(self) -> None:
        fields = set(InterviewState.model_fields.keys())
        assert "current_reasoning_decision" not in fields
        assert "progress" not in fields

    def test_follow_up_count_still_validated(self) -> None:
        with pytest.raises(ValidationError):
            _make_state(follow_up_count=99)

    def test_v12_fields_serialize_as_none_by_default(self) -> None:
        state = _make_state()
        d = state.model_dump()
        assert d["observation_store"] is None
        assert d["candidate_profile_v2"] is None
        assert d["session_history"] is None
        assert d["report"] is None

    def test_model_copy_preserves_v12_field_defaults(self) -> None:
        state = _make_state()
        new_state = state.model_copy(update={"follow_up_count": 1})
        assert new_state.observation_store is None
        assert new_state.candidate_profile_v2 is None
        assert new_state.session_history is None
        assert new_state.report is None


# ---------------------------------------------------------------------------
# Contract uniqueness — one class per domain concept
# ---------------------------------------------------------------------------

class TestContractUniqueness:
    def test_candidate_profile_v2_type_is_candidate_profile(self) -> None:
        annotation = InterviewStateBase.model_fields["candidate_profile_v2"].annotation
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
        """Exactly one class named CandidateProfile must exist in domain/contracts."""
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
# Sole-writer ownership guards
# ---------------------------------------------------------------------------

class TestSoleWriterOwnership:
    """Ownership guards: only declared sole-writer nodes may reference each field."""

    _NODES_DIR = Path("app/graph/nodes")

    def _nodes_referencing(self, field: str) -> list[str]:
        offenders = []
        for py_file in self._NODES_DIR.glob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            source = py_file.read_text()
            if field in source:
                offenders.append(py_file.name)
        return offenders

    def test_observation_store_sole_owner_nodes(self) -> None:
        """observation_store: sole writer = reasoner_node; permitted reader = session_close_node."""
        permitted = {"reasoner_node.py", "session_close_node.py"}
        offenders = set(self._nodes_referencing("observation_store")) - permitted
        assert offenders == set(), (
            f"Unexpected graph node(s) reference observation_store: {offenders}"
        )

    def test_candidate_profile_v2_sole_owner_nodes(self) -> None:
        """candidate_profile_v2: sole writer = reasoner_node; permitted reader = session_close_node."""
        permitted = {"reasoner_node.py", "session_close_node.py"}
        offenders = set(self._nodes_referencing("candidate_profile_v2")) - permitted
        assert offenders == set(), (
            f"Unexpected graph node(s) reference candidate_profile_v2: {offenders}"
        )

    def test_session_history_sole_owner_nodes(self) -> None:
        """session_history: sole writer = session_close_node; permitted readers = report_node, longitudinal_update_node.
        replay_node.py references SessionHistory (domain type) read-only — not InterviewState.session_history (EPIC-03 Phase 4a).
        """
        permitted = {
            "session_close_node.py",
            "report_node.py",
            "longitudinal_update_node.py",
            "replay_node.py",
        }
        offenders = set(self._nodes_referencing("session_history")) - permitted
        assert offenders == set(), (
            f"Unexpected graph node(s) reference session_history: {offenders}"
        )
