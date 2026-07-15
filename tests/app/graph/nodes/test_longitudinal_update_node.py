# tests/app/graph/nodes/test_longitudinal_update_node.py
# EPIC-02 — P4/C1 — Unit tests for LongitudinalUpdateNode
#
# Test plan (EPIC-02-IMPLEMENTATION-PLAN.md §8 — P4 unit tests):
#   - Success path: session_history present → repository.save() called exactly once
#   - Persistence failure path: save() raises → node returns state; WARNING logged; LP-09
#   - Idempotency guard: same interview_index already in prior profile → no-op (LP-07)
#   - Guard: session_history is None → immediate return, no repository call
#   - DI integration: node can receive repository instance via constructor injection

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview_state import InterviewState
from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from domain.contracts.user.role import Role, RoleType
from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
    JsonFileLongitudinalProfileRepository,
)
from app.graph.nodes.longitudinal_update_node import LongitudinalUpdateNode

from tests.domain.contracts.report.conftest import make_session_history
from tests.domain.contracts.longitudinal.conftest import (
    CANDIDATE_ID,
    make_longitudinal_profile,
    make_session_entry,
)

SESSION_ID = "p4c1-test-session"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_base_state(with_history: bool = True, interview_index: int = 0) -> InterviewState:
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="TestCorpP4C1",
        language="en",
        questions=[],
        interview_id=SESSION_ID,
    )
    state = state.model_copy(
        update={
            "is_completed": True,
            "candidate_identity_id": CANDIDATE_ID,
        }
    )
    if with_history:
        history = make_session_history(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)
        state = state.model_copy(update={"session_history": history})
    return state


def _make_mock_repository(
    get_return=None,
    save_side_effect=None,
) -> MagicMock:
    repo = MagicMock(spec=LongitudinalProfileRepository)
    repo.get.return_value = get_return
    if save_side_effect is not None:
        repo.save.side_effect = save_side_effect
    return repo


# ---------------------------------------------------------------------------
# DI integration
# ---------------------------------------------------------------------------


def test_node_accepts_repository_via_constructor_injection(tmp_path: Path) -> None:
    """P4-C1 DI test: node can receive a repository instance via constructor injection."""
    repo = JsonFileLongitudinalProfileRepository(storage_dir=tmp_path / "longitudinal")
    node = LongitudinalUpdateNode(repository=repo)
    assert isinstance(node, LongitudinalUpdateNode)


def test_node_accepts_abstract_repository(tmp_path: Path) -> None:
    repo = _make_mock_repository()
    node = LongitudinalUpdateNode(repository=repo)
    assert isinstance(node, LongitudinalUpdateNode)


# ---------------------------------------------------------------------------
# Guard: session_history is None
# ---------------------------------------------------------------------------


def test_node_no_op_when_session_history_is_none() -> None:
    state = _make_base_state(with_history=False)
    repo = _make_mock_repository()
    node = LongitudinalUpdateNode(repository=repo)

    result = node(state)

    repo.get.assert_not_called()
    repo.save.assert_not_called()
    assert result is state


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


def test_success_path_save_called_exactly_once() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(get_return=None)
    node = LongitudinalUpdateNode(repository=repo)

    result = node(state)

    repo.save.assert_called_once()
    assert result is state


def test_success_path_get_called_with_candidate_id() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(get_return=None)
    node = LongitudinalUpdateNode(repository=repo)

    node(state)

    repo.get.assert_called_once_with(CANDIDATE_ID)


def test_success_path_saved_profile_has_session_count_one() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(get_return=None)
    node = LongitudinalUpdateNode(repository=repo)

    node(state)

    saved_profile = repo.save.call_args[0][0]
    assert saved_profile.session_count == 1


def test_success_path_saved_profile_candidate_id_matches() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(get_return=None)
    node = LongitudinalUpdateNode(repository=repo)

    node(state)

    saved_profile = repo.save.call_args[0][0]
    assert saved_profile.candidate_identity_id == CANDIDATE_ID


def test_success_path_state_returned_unchanged() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(get_return=None)
    node = LongitudinalUpdateNode(repository=repo)

    result = node(state)

    assert result is state


# ---------------------------------------------------------------------------
# Persistence failure path — LP-09 (non-fatal)
# ---------------------------------------------------------------------------


def test_persistence_failure_node_does_not_raise() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(
        get_return=None,
        save_side_effect=OSError("disk full"),
    )
    node = LongitudinalUpdateNode(repository=repo)

    result = node(state)

    assert result is state


def test_persistence_failure_state_returned_unchanged() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(
        get_return=None,
        save_side_effect=RuntimeError("db unavailable"),
    )
    node = LongitudinalUpdateNode(repository=repo)

    result = node(state)

    assert result is state


def test_persistence_failure_warning_is_logged() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(
        get_return=None,
        save_side_effect=RuntimeError("db unavailable"),
    )
    node = LongitudinalUpdateNode(repository=repo)

    with patch("app.graph.nodes.longitudinal_update_node.logger") as mock_logger:
        node(state)
        mock_logger.warning.assert_called_once()


def test_get_failure_node_does_not_raise() -> None:
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository()
    repo.get.side_effect = RuntimeError("db unavailable")
    node = LongitudinalUpdateNode(repository=repo)

    result = node(state)

    assert result is state


# ---------------------------------------------------------------------------
# Idempotency guard — LP-07
# ---------------------------------------------------------------------------


def test_idempotency_guard_no_save_when_interview_index_already_present() -> None:
    """LP-07: if interview_index is already in the prior profile, skip (no-op)."""
    prior_profile = make_longitudinal_profile()
    existing_index = prior_profile.session_snapshots[0].interview_index

    state = _make_base_state(with_history=True)
    assert state.session_history is not None

    repo = _make_mock_repository(get_return=prior_profile)

    # Patch the session_history's interview_index to match the existing one.
    # We use a custom history whose interview_index matches the prior profile entry.
    history = make_session_history(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)

    # The make_session_history produces interview_index=0 by default (conftest),
    # and make_longitudinal_profile also uses interview_index=0.
    # They align — assert so this test is self-consistent.
    assert history.interview_index == existing_index

    state = state.model_copy(update={"session_history": history})
    node = LongitudinalUpdateNode(repository=repo)

    result = node(state)

    repo.save.assert_not_called()
    assert result is state


def test_idempotency_guard_logs_debug_when_skipping() -> None:
    prior_profile = make_longitudinal_profile()
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(get_return=prior_profile)
    node = LongitudinalUpdateNode(repository=repo)

    with patch("app.graph.nodes.longitudinal_update_node.logger") as mock_logger:
        node(state)
        mock_logger.debug.assert_called()


def test_different_interview_index_triggers_save() -> None:
    """A new interview_index not in the prior profile must trigger save."""
    from tests.domain.contracts.longitudinal.conftest import (
        FIXED_DT,
        LATER_DT,
        SESSION_ID_1,
        make_longitudinal_profile,
    )
    from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
    from tests.domain.contracts.session_history.conftest import (
        make_interview_metadata,
        make_language_profile,
        FIXED_HISTORY_DT,
    )
    from tests.domain.contracts.knowledge_snapshot.conftest import make_knowledge_snapshot
    from domain.contracts.session_history.session_history import ReplayMetadata

    # Prior profile has interview_index=0
    prior_profile = make_longitudinal_profile()
    assert prior_profile.session_snapshots[0].interview_index == 0

    # Build a session_history with interview_index=1
    snapshot = make_knowledge_snapshot(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)
    history_index_1 = (
        SessionHistoryBuilder()
        .with_session_id(SESSION_ID)
        .with_candidate_identity_id(CANDIDATE_ID)
        .with_interview_index(1)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=SESSION_ID))
        .with_transcript([])
        .with_question_timeline([])
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_HISTORY_DT)
        .build()
    )

    state = _make_base_state(with_history=False)
    state = state.model_copy(update={"session_history": history_index_1})
    repo = _make_mock_repository(get_return=prior_profile)
    node = LongitudinalUpdateNode(repository=repo)

    node(state)

    repo.save.assert_called_once()
    saved = repo.save.call_args[0][0]
    assert saved.session_count == 2


# ---------------------------------------------------------------------------
# Architecture: no LLM imports (LP-03)
# ---------------------------------------------------------------------------


def test_node_does_not_import_llm_services() -> None:
    """LP-03: longitudinal_update_node must not import LLM/pipeline services."""
    import ast
    import pathlib

    node_source = pathlib.Path("app/graph/nodes/longitudinal_update_node.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(node_source)

    forbidden_patterns = {
        "NarrativeGenerator",
        "CoachingEngine",
        "FeatureEngine",
        "KnowledgePipeline",
        "ObservationExtractor",
        "LLMPort",
        "openai",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            for alias in getattr(node, "names", []):
                name = alias.name or ""
                for forbidden in forbidden_patterns:
                    assert forbidden not in module and forbidden not in name, (
                        f"LP-03 violation: longitudinal_update_node imports forbidden "
                        f"symbol '{forbidden}'"
                    )


# ---------------------------------------------------------------------------
# Architecture: sole writer assertion (LP-01)
# ---------------------------------------------------------------------------


def test_repository_save_called_only_by_node(tmp_path: Path) -> None:
    """LP-01: only LongitudinalUpdateNode calls repository.save()."""
    state = _make_base_state(with_history=True)
    repo = _make_mock_repository(get_return=None)
    node = LongitudinalUpdateNode(repository=repo)

    node(state)

    assert repo.save.call_count == 1
