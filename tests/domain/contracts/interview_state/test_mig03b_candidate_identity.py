# tests/domain/contracts/interview_state/test_mig03b_candidate_identity.py
# MIG-03B — candidate_identity_id TCP field tests (RIB-01, PAT-04, ADR-016A)
#
# Verifies:
# 1. candidate_identity_id is present on InterviewState with correct type.
# 2. create_initial always produces a non-null, stable candidate_identity_id.
# 3. create_empty always produces a non-null candidate_identity_id.
# 4. Same interview_id always produces same candidate_identity_id (deterministic).
# 5. Different interview_ids produce different candidate_identity_ids.
# 6. candidate_identity_id is immutable across model_copy cycles.
# 7. Legacy states (candidate_identity_id=None) are accepted (backward compat).
# 8. No V1.1 node reads candidate_identity_id (architectural guard).
# 9. reasoner_node._resolve_candidate_identity_id returns identity from state.
# 10. Fallback to interview_id when candidate_identity_id is None (legacy compat).

from __future__ import annotations

import ast
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

import pytest

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_state.base import InterviewStateBase
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import Role, RoleType
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_kwargs() -> dict:
    return {
        "interview_id": "mig03b-test",
        "role": Role(type=RoleType.BACKEND_ENGINEER),
        "company": "ACME",
    }


def _minimal_state(**overrides) -> InterviewState:
    kwargs = _base_kwargs()
    kwargs.update(overrides)
    return InterviewState(**kwargs)


def _minimal_question() -> Question:
    return Question(
        id="q1",
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt="Write a function",
        difficulty=QuestionDifficulty.MEDIUM,
    )


def _create_initial(interview_id: str = "session-test-001") -> InterviewState:
    return InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="ACME",
        language="en",
        questions=[_minimal_question()],
        interview_id=interview_id,
    )


# ---------------------------------------------------------------------------
# 1. Field presence and type
# ---------------------------------------------------------------------------

class TestFieldPresence:

    def test_field_on_base_model(self):
        fields = InterviewStateBase.model_fields
        assert "candidate_identity_id" in fields

    def test_field_default_is_none(self):
        fields = InterviewStateBase.model_fields
        assert fields["candidate_identity_id"].default is None

    def test_field_annotation_allows_none(self):
        state = _minimal_state()
        assert state.candidate_identity_id is None

    def test_field_accepts_string(self):
        state = _minimal_state(candidate_identity_id="explicit-id-abc")
        assert state.candidate_identity_id == "explicit-id-abc"

    def test_field_description_contains_tcp_marker(self):
        field = InterviewStateBase.model_fields["candidate_identity_id"]
        description = field.metadata[0].description if field.metadata else (field.description if hasattr(field, "description") else "")
        # Check via the json_schema_extra or description kwarg on Field
        # Access via model_fields metadata
        assert "[V1.2 TCP]" in str(field)


# ---------------------------------------------------------------------------
# 2. create_initial — non-null, stable, deterministic
# ---------------------------------------------------------------------------

class TestCreateInitial:

    def test_candidate_identity_id_is_not_none(self):
        state = _create_initial()
        assert state.candidate_identity_id is not None

    def test_candidate_identity_id_is_non_empty_string(self):
        state = _create_initial()
        assert isinstance(state.candidate_identity_id, str)
        assert len(state.candidate_identity_id) > 0

    def test_candidate_identity_id_is_deterministic(self):
        id1 = _create_initial("session-abc").candidate_identity_id
        id2 = _create_initial("session-abc").candidate_identity_id
        assert id1 == id2

    def test_candidate_identity_id_differs_per_session(self):
        id1 = _create_initial("session-aaa").candidate_identity_id
        id2 = _create_initial("session-bbb").candidate_identity_id
        assert id1 != id2

    def test_candidate_identity_id_matches_uuid5_derivation(self):
        interview_id = "session-deterministic-001"
        state = _create_initial(interview_id)
        expected = str(uuid5(NAMESPACE_URL, f"candidate:{interview_id}"))
        assert state.candidate_identity_id == expected

    def test_candidate_identity_id_stable_across_model_copy(self):
        state = _create_initial("session-stable")
        original_id = state.candidate_identity_id
        updated = state.model_copy(update={"current_question_index": 1})
        assert updated.candidate_identity_id == original_id


# ---------------------------------------------------------------------------
# 3. create_empty — non-null identity
# ---------------------------------------------------------------------------

class TestCreateEmpty:

    def test_candidate_identity_id_is_not_none(self):
        state = InterviewState.create_empty()
        assert state.candidate_identity_id is not None

    def test_candidate_identity_id_is_non_empty_string(self):
        state = InterviewState.create_empty()
        assert isinstance(state.candidate_identity_id, str)
        assert len(state.candidate_identity_id) > 0

    def test_two_empty_states_have_different_identity_ids(self):
        s1 = InterviewState.create_empty()
        s2 = InterviewState.create_empty()
        # Different sessions → different identities
        if s1.interview_id != s2.interview_id:
            assert s1.candidate_identity_id != s2.candidate_identity_id


# ---------------------------------------------------------------------------
# 4. Backward compatibility — legacy states with None
# ---------------------------------------------------------------------------

class TestBackwardCompat:

    def test_state_without_identity_is_valid(self):
        state = _minimal_state()
        assert state.candidate_identity_id is None

    def test_extra_forbid_still_enforced(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            InterviewState(**_base_kwargs(), _unknown_field="x")

    def test_v11_fields_unaffected(self):
        state = _minimal_state()
        assert state.observation_store is None
        assert state.candidate_profile_v2 is None
        assert state.session_history is None


# ---------------------------------------------------------------------------
# 5. Architectural guard — no V1.1 node reads candidate_identity_id directly
# ---------------------------------------------------------------------------

class TestArchitecturalGuard:

    def _node_sources(self) -> list[Path]:
        nodes_dir = Path(__file__).parents[4] / "app" / "graph" / "nodes"
        return list(nodes_dir.glob("*.py"))

    def test_no_node_references_candidate_identity_id_except_reasoner(self):
        """Only reasoner_node may reference candidate_identity_id (via helper)."""
        for path in self._node_sources():
            if path.name == "reasoner_node.py":
                continue
            source = path.read_text(encoding="utf-8")
            assert "candidate_identity_id" not in source, (
                f"{path.name} must not reference candidate_identity_id directly"
            )

    def test_reasoner_node_uses_resolver_helper(self):
        """reasoner_node must use _resolve_candidate_identity_id, not raw field."""
        nodes_dir = Path(__file__).parents[4] / "app" / "graph" / "nodes"
        reasoner = (nodes_dir / "reasoner_node.py").read_text(encoding="utf-8")
        assert "_resolve_candidate_identity_id" in reasoner


# ---------------------------------------------------------------------------
# 6. Identity propagation — _resolve_candidate_identity_id behaviour
# ---------------------------------------------------------------------------

class TestIdentityResolution:

    def _import_resolver(self):
        from app.graph.nodes.reasoner_node import _resolve_candidate_identity_id
        return _resolve_candidate_identity_id

    def test_returns_candidate_identity_id_when_set(self):
        resolver = self._import_resolver()
        state = _create_initial("session-resolve-test")
        resolved = resolver(state)
        assert resolved == state.candidate_identity_id

    def test_fallback_to_interview_id_when_none(self):
        resolver = self._import_resolver()
        state = _minimal_state()
        assert state.candidate_identity_id is None
        resolved = resolver(state)
        assert resolved == state.interview_id

    def test_resolved_id_is_non_empty(self):
        resolver = self._import_resolver()
        state = _create_initial("session-nonempty")
        assert len(resolver(state)) > 0

    def test_resolved_id_stable_across_cycles(self):
        resolver = self._import_resolver()
        state = _create_initial("session-stable-cycle")
        id1 = resolver(state)
        id2 = resolver(state)
        assert id1 == id2
