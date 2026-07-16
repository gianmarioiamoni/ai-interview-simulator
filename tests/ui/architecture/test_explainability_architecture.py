# tests/ui/architecture/test_explainability_architecture.py
# EPIC-06 M2 / C4 — architectural enforcement for explainability projection invariants.
# AT-02 dual-read ban · AT-03 LLM-free path · AT-06 silent-omit forbidden

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ui.dto.final_report_dto import (
    CoachingActionDTO,
    FeatureIdentityDTO,
    FinalReportDTO,
    NarrativeInsightDTO,
    _assert_explainability_projection_complete,
)
from domain.contracts.coaching.coaching_action import ActionCategory, CoachingAction
from domain.contracts.coaching.coaching_builder import CoachingBuilder
from tests.domain.contracts.report.conftest import (
    make_report,
    make_report_with_explainability,
)
from tests.domain.contracts.session_history.conftest import SESSION_ID

REPO_ROOT = Path(__file__).resolve().parents[3]

# Explainability projection path (DTO plane). UI/export consumers are out of C4 scope.
EXPLAINABILITY_PROJECTION_MODULES = (
    "app/ui/dto/final_report_dto.py",
)

FORBIDDEN_DUAL_READ_IMPORTS = {
    "SessionHistory",
    "ObservationStore",
    "Observation",
    "ObservationSnapshot",
    "ObservationQuery",
    "ObservationFilter",
}

FORBIDDEN_DUAL_READ_MODULE_FRAGMENTS = (
    "session_history",
    "observation_store",
    "observation.observation_store",
    "observation.observation_query",
    "observation.observation_snapshot",
)

FORBIDDEN_LLM_IMPORTS = {
    "openai",
    "anthropic",
    "langchain",
    "langchain_openai",
    "langchain_core",
    "LLM",
    "ChatOpenAI",
    "ChatAnthropic",
    "llm_client",
    "LLMClient",
}

FORBIDDEN_LLM_MODULE_FRAGMENTS = (
    "openai",
    "anthropic",
    "langchain",
    "llm_client",
    "llm.",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _imported_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
                names.add(alias.name.split(".")[0])
                if alias.asname:
                    names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
                names.add(node.module.split(".")[0])
            for alias in node.names:
                names.add(alias.name)
                if alias.asname:
                    names.add(alias.asname)
    return names


def _from_report_executable_source() -> str:
    source = _read("app/ui/dto/final_report_dto.py")
    tree = ast.parse(source)
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "FinalReportDTO"
    )
    from_report = next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "from_report"
    )
    body_nodes = list(from_report.body)
    if (
        body_nodes
        and isinstance(body_nodes[0], ast.Expr)
        and isinstance(body_nodes[0].value, ast.Constant)
    ):
        body_nodes = body_nodes[1:]
    return ast.unparse(ast.Module(body=body_nodes, type_ignores=[]))


class TestExplainabilityDualReadBan:
    """AT-02 — no SessionHistory / Observation-store reads on explainability path."""

    @pytest.mark.parametrize("relative_path", EXPLAINABILITY_PROJECTION_MODULES)
    def test_module_does_not_import_session_history_or_observation_store(
        self, relative_path: str
    ) -> None:
        source = _read(relative_path)
        imported = _imported_names(source)
        for name in FORBIDDEN_DUAL_READ_IMPORTS:
            assert name not in imported, (
                f"Forbidden dual-read import {name!r} in {relative_path}"
            )
        for fragment in FORBIDDEN_DUAL_READ_MODULE_FRAGMENTS:
            assert not any(fragment in name for name in imported), (
                f"Forbidden dual-read module fragment {fragment!r} in {relative_path}"
            )

    def test_from_report_signature_is_report_only(self) -> None:
        params = [
            name
            for name in inspect.signature(FinalReportDTO.from_report).parameters
            if name not in {"cls", "self"}
        ]
        assert params == ["report"]

    def test_from_report_body_has_no_session_history_or_observation_store_access(
        self,
    ) -> None:
        body = _from_report_executable_source()
        assert "SessionHistory" not in body
        assert "session_history" not in body
        assert "ObservationStore" not in body
        assert "observation_store" not in body


class TestExplainabilityLlmFreePath:
    """AT-03 — no LLM/client calls on explainability projection path (ARC-01)."""

    @pytest.mark.parametrize("relative_path", EXPLAINABILITY_PROJECTION_MODULES)
    def test_module_does_not_import_llm_clients(self, relative_path: str) -> None:
        source = _read(relative_path)
        imported = _imported_names(source)
        for name in FORBIDDEN_LLM_IMPORTS:
            assert name not in imported, (
                f"Forbidden LLM import {name!r} in {relative_path}"
            )
        for fragment in FORBIDDEN_LLM_MODULE_FRAGMENTS:
            assert not any(fragment in name for name in imported), (
                f"Forbidden LLM module fragment {fragment!r} in {relative_path}"
            )

    def test_from_report_body_has_no_llm_invocation(self) -> None:
        body = _from_report_executable_source()
        for token in (
            "openai",
            "anthropic",
            "langchain",
            "ChatOpenAI",
            "llm_client",
            ".invoke(",
            ".ainvoke(",
            "generate(",
        ):
            assert token not in body, f"Forbidden LLM token {token!r} in from_report"


class TestExplainabilitySilentOmitForbidden:
    """AT-06 — missing required anchors fail-fast; no silent drop / soft-hide."""

    def test_from_report_invokes_projection_completeness_gate(self) -> None:
        body = _from_report_executable_source()
        assert "_assert_explainability_projection_complete" in body

    def test_from_report_does_not_catch_explainability_errors(self) -> None:
        """Fail-fast must not be softened by try/except around projection."""
        source = _read("app/ui/dto/final_report_dto.py")
        tree = ast.parse(source)
        class_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "FinalReportDTO"
        )
        from_report = next(
            node
            for node in class_node.body
            if isinstance(node, ast.FunctionDef) and node.name == "from_report"
        )
        try_nodes = [
            node for node in ast.walk(from_report) if isinstance(node, ast.Try)
        ]
        assert try_nodes == [], (
            "from_report must not catch projection failures (silent-omit risk)"
        )

    def test_incomplete_insight_does_not_soft_hide_to_empty_list(self) -> None:
        incomplete = NarrativeInsightDTO(
            insight_type="strength_signal",
            prose="x",
            confidence=0.5,
            source_feature_id=FeatureIdentityDTO(
                feature_type_id="",
                semantic_category="analytical_reasoning",
            ),
            is_traceable=True,
        )
        with patch(
            "app.ui.dto.final_report_dto._map_narrative_insight",
            return_value=incomplete,
        ):
            report = make_report_with_explainability()
            with pytest.raises(ValueError, match="X-01"):
                FinalReportDTO.from_report(report)

    def test_incomplete_action_origin_does_not_soft_hide_to_empty_list(self) -> None:
        incomplete = CoachingActionDTO(
            action_id="act-1",
            objective_id="obj-1",
            category="practice",
            description="Drill",
            effort_estimate_hours=1.0,
            is_immediate=False,
            origin_feature_type="",
            origin_supporting_observation_types=[],
            origin_objective_description="Objective",
        )
        with patch(
            "app.ui.dto.final_report_dto._map_coaching_actions",
            return_value=[incomplete],
        ):
            report = make_report_with_explainability()
            with pytest.raises(ValueError, match="X-04"):
                FinalReportDTO.from_report(report)

    def test_unresolved_objective_does_not_drop_action_silently(self) -> None:
        orphan = CoachingAction(
            action_id="act-orphan",
            objective_id="obj-missing",
            category=ActionCategory.PRACTICE,
            description="Orphan action",
            effort_estimate_hours=1.0,
            is_immediate=False,
        )
        report = make_report().model_copy(
            update={
                "coaching_snapshot": CoachingBuilder.build(
                    objectives=(),
                    actions=(orphan,),
                    recommendations=(),
                    session_id=SESSION_ID,
                    question_index=0,
                )
            }
        )
        with pytest.raises(ValueError, match="objective_id"):
            FinalReportDTO.from_report(report)

    def test_gate_rejects_missing_anchor_instead_of_omitting(self) -> None:
        with pytest.raises(ValueError, match="X-02"):
            _assert_explainability_projection_complete(
                [
                    NarrativeInsightDTO(
                        insight_type="strength_signal",
                        prose="x",
                        confidence=0.5,
                        source_feature_id=FeatureIdentityDTO(
                            feature_type_id="reasoning_feature",
                            semantic_category="analytical_reasoning",
                        ),
                        is_traceable=False,
                    )
                ],
                [],
            )
