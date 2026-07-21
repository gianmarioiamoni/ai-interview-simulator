# tests/domain/contracts/interview_state/test_epic10_ownership_matrix.py
#
# EPIC-10 Macro B / P2 — AT-01 Ownership Matrix coverage + writer presence.
# Consumes docs/master-plan/epics/EPIC-10-OWNERSHIP-MATRIX.json (Contracts §4 / EC-IS-01).

from __future__ import annotations

import json
import re
from pathlib import Path

from domain.contracts.interview_state import InterviewState

REPO_ROOT = Path(__file__).resolve().parents[4]
MATRIX_PATH = (
    REPO_ROOT / "docs" / "master-plan" / "epics" / "EPIC-10-OWNERSHIP-MATRIX.json"
)
NODES_DIR = REPO_ROOT / "app" / "graph" / "nodes"
FACTORY_PATH = (
    REPO_ROOT / "domain" / "contracts" / "interview_state" / "factory.py"
)

# Graph-node writer tokens → module file under app/graph/nodes/.
NODE_WRITER_FILES: dict[str, str] = {
    "adaptive_navigation_node": "adaptive_navigation_node.py",
    "adaptive_nav": "adaptive_navigation_node.py",
    "reasoner_node": "reasoner_node.py",
    "evaluation_node": "evaluation_node.py",
    "execution_node": "execution_node.py",
    "written_evaluation_node": "written_evaluation_node.py",
    "hint_node": "hint_node.py",
    "feedback_node": "feedback_node.py",
    "question_node": "question_node.py",
    "evaluation_aggregate_node": "evaluation_aggregate_node.py",
    "eval_agg": "evaluation_aggregate_node.py",
    "session_close_node": "session_close_node.py",
    "report_node": "report_node.py",
    "decision_node": "decision_node.py",
    "completion_node": "completion_node.py",
    "start_processing_node": "start_processing_node.py",
    "start_processing": "start_processing_node.py",
    "execution": "execution_node.py",
    "evaluation": "evaluation_node.py",
    "feedback": "feedback_node.py",
    "report": "report_node.py",
}

# Sole-writer fields with strong prior arch coverage — undeclared node refs forbidden.
SOLE_WRITER_REFERENCE_ALLOWLIST: dict[str, frozenset[str]] = {
    "observation_store": frozenset({"reasoner_node.py", "session_close_node.py"}),
    "candidate_profile_v2": frozenset({"reasoner_node.py", "session_close_node.py"}),
    "session_history": frozenset(
        {
            "session_close_node.py",
            "report_node.py",
            "longitudinal_update_node.py",
            "replay_node.py",
        }
    ),
    "report": frozenset({"report_node.py"}),
    "interview_memory": frozenset({"reasoner_node.py"}),
}


def _load_matrix() -> dict:
    assert MATRIX_PATH.is_file(), f"Missing ownership matrix: {MATRIX_PATH}"
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def _matrix_fields(matrix: dict) -> list[dict]:
    fields = matrix["fields"]
    assert isinstance(fields, list)
    return fields


def _nodes_referencing(field: str) -> set[str]:
    """Match field as a string key or attribute — not an arbitrary substring."""
    pattern = re.compile(rf'(["\']{re.escape(field)}["\']|\.{re.escape(field)}\b)')
    hits: set[str] = set()
    for py_file in NODES_DIR.glob("*.py"):
        if pattern.search(py_file.read_text(encoding="utf-8")):
            hits.add(py_file.name)
    return hits


class TestAT01MatrixCompleteness:
    """AT-01 / I-OM-01 — every InterviewState field appears exactly once with writers."""

    def test_matrix_field_count_is_45(self) -> None:
        matrix = _load_matrix()
        assert matrix["field_count"] == 45
        assert len(_matrix_fields(matrix)) == 45

    def test_matrix_covers_all_interview_state_fields(self) -> None:
        matrix_names = {row["field"] for row in _matrix_fields(_load_matrix())}
        state_names = set(InterviewState.model_fields.keys())
        assert matrix_names == state_names, (
            f"Missing from matrix: {sorted(state_names - matrix_names)}; "
            f"extra in matrix: {sorted(matrix_names - state_names)}"
        )

    def test_each_field_appears_exactly_once(self) -> None:
        names = [row["field"] for row in _matrix_fields(_load_matrix())]
        assert len(names) == len(set(names))

    def test_every_field_has_non_empty_authorized_writers(self) -> None:
        for row in _matrix_fields(_load_matrix()):
            writers = row.get("authorized_writers")
            assert isinstance(writers, list) and len(writers) > 0, (
                f"{row.get('field')}: authorized_writers must be non-empty"
            )

    def test_candidate_profile_v2_ownership_only(self) -> None:
        row = next(
            r for r in _matrix_fields(_load_matrix()) if r["field"] == "candidate_profile_v2"
        )
        assert row["authorized_writers"] == ["reasoner_node"]
        assert "Ownership only" in row.get("notes", "")


class TestAT01WriterPresence:
    """AT-01 — declared graph-node writers exist; sole-writer allowlists hold."""

    def test_declared_node_writers_have_modules(self) -> None:
        missing: list[str] = []
        for row in _matrix_fields(_load_matrix()):
            for writer in row["authorized_writers"]:
                module_name = NODE_WRITER_FILES.get(writer)
                if module_name is None:
                    continue
                if not (NODES_DIR / module_name).is_file():
                    missing.append(f"{row['field']}:{writer}->{module_name}")
        assert missing == [], f"Missing writer modules: {missing}"

    def test_factory_writer_fields_initialized_in_factory(self) -> None:
        factory_source = FACTORY_PATH.read_text(encoding="utf-8")
        for row in _matrix_fields(_load_matrix()):
            if "Factory" not in row["authorized_writers"]:
                continue
            field = row["field"]
            assert field in factory_source, (
                f"Factory-authorized field {field!r} not referenced in factory.py"
            )

    def test_sole_writer_reference_allowlists(self) -> None:
        for field, permitted in SOLE_WRITER_REFERENCE_ALLOWLIST.items():
            offenders = _nodes_referencing(field) - permitted
            assert offenders == set(), (
                f"Unexpected graph node(s) reference {field}: {offenders}"
            )

    def test_asked_question_ids_top_level_write_in_adaptive_navigation(self) -> None:
        """C5 alignment — NEXT path writes top-level asked_question_ids (not nested only)."""
        source = (NODES_DIR / "adaptive_navigation_node.py").read_text(encoding="utf-8")
        assert '"asked_question_ids": asked_question_ids' in source
        assert "list(state.asked_question_ids)" in source
