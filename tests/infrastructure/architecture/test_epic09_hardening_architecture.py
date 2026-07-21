# tests/infrastructure/architecture/test_epic09_hardening_architecture.py
#
# EPIC-09 P7/C10 — Category A / ARC-01 hardening (Freeze CAT-*, ARC-*, O-02).
# Enforces: no SessionHistory store, no domain caches, no InterviewState
# measurement fields, no LangGraph topology drift, no compute-in-projection.

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from domain.contracts.interview_state import InterviewState
from domain.contracts.session_history.session_history import SessionHistory

REPO_ROOT = Path(__file__).resolve().parents[3]

_SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "node_modules",
        ".ruff_cache",
    }
)

# CAT-09 authorized EPIC-09 code surfaces (harness + optional infra emit).
EPIC09_SURFACE_ROOTS: tuple[str, ...] = (
    "tests/performance",
    "scripts/performance",
)

EPIC09_INFRA_FILES: frozenset[str] = frozenset(
    {
        "infrastructure/observability/question_cycle_logging.py",
    }
)

# CAT-05 / AR-21 — frozen interview graph node names (EPIC-09 must not expand).
FROZEN_INTERVIEW_GRAPH_NODES: frozenset[str] = frozenset(
    {
        "entry",
        "router",
        "navigation",
        "question",
        "execution",
        "evaluation",
        "evaluation_aggregate",
        "feedback",
        "reasoner",
        "hint",
        "decision",
        "written",
        "completion",
        "session_close",
        "report",
        "longitudinal_update",
        "start_processing",
    }
)

# CAT-04 / AR-08 — frozen InterviewState field set (no measurement fields).
FROZEN_INTERVIEW_STATE_FIELDS: frozenset[str] = frozenset(
    {
        "adaptive_interview_enabled",
        "allowed_actions",
        "answers",
        "asked_question_ids",
        "awaiting_user_input",
        "candidate_identity_id",
        "candidate_profile_v2",
        "chat_history",
        "company",
        "context_profile",
        "current_progress",
        "current_question_index",
        "current_step",
        "dimension_signals",
        "enable_humanizer",
        "events",
        "follow_up_count",
        "follow_up_eligible_indices",
        "intent",
        "interview_cost_metrics",
        "interview_id",
        "interview_length",
        "interview_memory",
        "interview_metrics",
        "interview_type",
        "is_completed",
        "is_processing",
        "language",
        "last_feedback_bundle",
        "last_humanizer_follow_up",
        "last_question_context",
        "observation_store",
        "planned_areas",
        "question_display_text",
        "questions",
        "report",
        "results_by_question",
        "retrieval_memory",
        "role",
        "scoring_narrative",
        "scoring_snapshot",
        "seniority_level",
        "session_history",
    }
)

FORBIDDEN_MEASUREMENT_FIELD_TOKENS: frozenset[str] = frozenset(
    {
        "cycle_latency",
        "duration_ms",
        "question_cycle",
        "slo_q",
        "slo_r",
        "slo_p",
        "latency_ms",
        "p99",
    }
)

# ARC-01 / ARC-02 / AR-13 — compute services must stay out of projection.
PROJECTION_MODULES: tuple[str, ...] = (
    "app/graph/nodes/report_node.py",
    "app/ui/dto/final_report_dto.py",
)

FORBIDDEN_COMPUTE_IMPORT_FRAGMENTS: frozenset[str] = frozenset(
    {
        "feature_engine",
        "FeatureEngine",
        "knowledge_pipeline",
        "KnowledgePipeline",
        "narrative_generator",
        "NarrativeGenerator",
        "coaching_engine",
        "CoachingEngine",
        "observation_extractor",
        "ObservationExtractor",
    }
)

FORBIDDEN_CACHE_MODULE_ROOTS: frozenset[str] = frozenset(
    {
        "redis",
        "cachetools",
    }
)

# CAT-06 / AR-06 — SessionHistory durable store surfaces (not general SQLite).
FORBIDDEN_SESSION_HISTORY_STORE_GLOBS: tuple[str, ...] = (
    "**/session_history_store.py",
    "**/session_history_repository.py",
    "**/session_history_db.py",
    "infrastructure/persistence/**/session_history*.py",
    "domain/persistence/**",
    "domain/contracts/performance/**",
    "domain/contracts/metrics/**",
)

FORBIDDEN_DOMAIN_CACHE_TARGET_NAMES: frozenset[str] = frozenset(
    {
        "ReplaySession",
        "LongitudinalProfile",
        "SessionHistory",
    }
)


def _iter_py_under(relative_root: str) -> list[Path]:
    root = REPO_ROOT / relative_root
    if not root.exists():
        return []
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    return sorted(
        p
        for p in root.rglob("*.py")
        if not any(part in _SKIP_DIR_NAMES for part in p.relative_to(REPO_ROOT).parts)
    )


def _epic09_surface_files() -> list[Path]:
    files: list[Path] = []
    for root in EPIC09_SURFACE_ROOTS:
        files.extend(_iter_py_under(root))
    for relative in EPIC09_INFRA_FILES:
        path = REPO_ROOT / relative
        if path.is_file():
            files.append(path)
    return sorted(set(files))


def _replay_ui_modules() -> list[str]:
    root = REPO_ROOT / "app" / "ui" / "replay"
    return sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in root.rglob("*.py")
        if p.name != "__init__.py"
        and not any(part in _SKIP_DIR_NAMES for part in p.relative_to(REPO_ROOT).parts)
    )


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def _imported_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
                names.add(node.module.split(".")[0])
            for alias in node.names:
                names.add(alias.name)
    return names


def _string_and_name_tokens(source: str) -> set[str]:
    tree = ast.parse(source)
    tokens: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.add(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            tokens.add(node.value)
    return tokens


def _add_node_literal_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_add_node = (
            isinstance(func, ast.Attribute) and func.attr == "add_node"
        ) or (isinstance(func, ast.Name) and func.id == "add_node")
        if not is_add_node or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            names.add(first.value)
        elif isinstance(first, ast.Name):
            names.add(first.id)
    return names


def _uses_lru_cache_or_cache_decorator(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in {"lru_cache", "cache"}:
            return True
        if isinstance(node, ast.Name) and node.id in {"lru_cache", "cache"}:
            return True
    return False


def _defines_class_named(source: str, names: frozenset[str]) -> list[str]:
    tree = ast.parse(source)
    return sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name in names
    )


class TestNoSessionHistoryStoreDrift:
    """CAT-06 / AR-06 — no SessionHistory durable store / schema additions."""

    def test_forbidden_session_history_store_paths_absent(self) -> None:
        hits: list[str] = []
        for pattern in FORBIDDEN_SESSION_HISTORY_STORE_GLOBS:
            for path in REPO_ROOT.glob(pattern):
                if any(part in _SKIP_DIR_NAMES for part in path.parts):
                    continue
                if path.is_file():
                    hits.append(path.relative_to(REPO_ROOT).as_posix())
                elif path.is_dir() and any(
                    p.suffix == ".py"
                    for p in path.rglob("*.py")
                    if not any(part in _SKIP_DIR_NAMES for part in p.parts)
                ):
                    hits.append(path.relative_to(REPO_ROOT).as_posix())
        assert hits == [], (
            f"CAT-06/AR-06 forbidden SessionHistory store paths: {hits}"
        )

    def test_session_history_schema_version_unchanged(self) -> None:
        assert SessionHistory.model_fields["schema_version"].default == "2.0"

    def test_epic09_surfaces_do_not_define_store_types(self) -> None:
        forbidden = frozenset(
            {
                "SessionHistoryStore",
                "SessionHistoryRepository",
                "ReplaySessionCache",
                "LongitudinalProfileCache",
            }
        )
        violations: list[str] = []
        for path in _epic09_surface_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            defined = _defines_class_named(
                path.read_text(encoding="utf-8"), forbidden
            )
            if defined:
                violations.append(f"{relative}: {defined}")
        assert violations == [], f"CAT-06 store types in EPIC-09 surfaces: {violations}"


class TestNoDomainCacheDrift:
    """CAT-07 / AR-07 — no ReplaySession / LongitudinalProfile / SessionHistory caches."""

    def test_epic09_surfaces_have_no_cache_backends(self) -> None:
        violations: list[str] = []
        for path in _epic09_surface_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            source = path.read_text(encoding="utf-8")
            imported = _imported_names(source)
            bad_roots = sorted(FORBIDDEN_CACHE_MODULE_ROOTS & imported)
            if bad_roots:
                violations.append(f"{relative}: imports {bad_roots}")
            if _uses_lru_cache_or_cache_decorator(source):
                violations.append(f"{relative}: lru_cache/cache decorator")
        assert violations == [], f"CAT-07/AR-07 cache drift: {violations}"

    def test_projection_modules_do_not_cache_domain_artifacts(self) -> None:
        modules = list(PROJECTION_MODULES) + _replay_ui_modules()
        violations: list[str] = []
        for relative in modules:
            source = _read(relative)
            if not _uses_lru_cache_or_cache_decorator(source):
                continue
            tokens = _string_and_name_tokens(source)
            cached_targets = sorted(FORBIDDEN_DOMAIN_CACHE_TARGET_NAMES & tokens)
            if cached_targets:
                violations.append(f"{relative}: cache near {cached_targets}")
            else:
                # Any cache decorator on projection is still out of EPIC-09 scope.
                violations.append(f"{relative}: cache decorator on projection")
        assert violations == [], f"O-02/AR-07 projection cache: {violations}"


class TestNoInterviewStateMeasurementDrift:
    """CAT-04 / AR-08 — no InterviewState fields for cycle correlation."""

    def test_interview_state_field_set_frozen(self) -> None:
        actual = frozenset(InterviewState.model_fields)
        assert actual == FROZEN_INTERVIEW_STATE_FIELDS, (
            "CAT-04: InterviewState field drift — "
            f"added={sorted(actual - FROZEN_INTERVIEW_STATE_FIELDS)} "
            f"removed={sorted(FROZEN_INTERVIEW_STATE_FIELDS - actual)}"
        )

    def test_no_measurement_field_tokens_on_interview_state(self) -> None:
        fields = set(InterviewState.model_fields)
        leaked = sorted(
            token
            for token in FORBIDDEN_MEASUREMENT_FIELD_TOKENS
            if any(token in field for field in fields)
        )
        assert leaked == [], f"AR-08 measurement fields on InterviewState: {leaked}"


class TestNoLangGraphTopologyDrift:
    """CAT-05 / AR-21 — no performance-driven topology changes."""

    def test_interview_graph_node_set_frozen(self) -> None:
        source = _read("app/graph/interview_graph.py")
        nodes = _add_node_literal_names(source)
        # Constant name reference for entry instrumentation uses string literals only.
        assert nodes == FROZEN_INTERVIEW_GRAPH_NODES, (
            "CAT-05/AR-21 interview topology drift — "
            f"added={sorted(nodes - FROZEN_INTERVIEW_GRAPH_NODES)} "
            f"removed={sorted(FROZEN_INTERVIEW_GRAPH_NODES - nodes)}"
        )

    def test_replay_graph_remains_single_node(self) -> None:
        source = _read("app/graph/replay_graph.py")
        nodes = _add_node_literal_names(source)
        # add_node may use _REPLAY_NODE_NAME Name; accept literal or name token.
        assert nodes == {"replay"} or nodes == {"_REPLAY_NODE_NAME"}, (
            f"AR-21 replay topology must remain sole replay node; got {nodes}"
        )
        assert 'graph.add_edge(_REPLAY_NODE_NAME, END)' in source
        assert "checkpointer=None" in source

    def test_epic09_surfaces_do_not_mutate_product_topology(self) -> None:
        violations: list[str] = []
        for path in _epic09_surface_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            source = path.read_text(encoding="utf-8")
            if "add_node(" in source or "StateGraph(" in source:
                violations.append(relative)
        assert violations == [], (
            "MEAS-07/AR-21: EPIC-09 harnesses must not build product topology: "
            f"{violations}"
        )


class TestNoComputeInProjection:
    """ARC-01 / ARC-02 / AR-13 / O-02 — projection remains non-computing."""

    @pytest.mark.parametrize(
        "relative",
        list(PROJECTION_MODULES) + _replay_ui_modules(),
    )
    def test_projection_module_has_no_compute_service_imports(
        self, relative: str
    ) -> None:
        source = _read(relative)
        imported = _imported_names(source)
        tokens = imported | _string_and_name_tokens(source)
        leaked = sorted(
            fragment
            for fragment in FORBIDDEN_COMPUTE_IMPORT_FRAGMENTS
            if fragment in tokens
            or any(fragment in name for name in imported)
        )
        # Domain contract type imports (CoachingAction, NarrativeInsight) are allowed
        # on DTO mapping; only service/engine compute symbols are forbidden.
        service_leaked = [
            item
            for item in leaked
            if item
            in {
                "feature_engine",
                "FeatureEngine",
                "knowledge_pipeline",
                "KnowledgePipeline",
                "narrative_generator",
                "NarrativeGenerator",
                "coaching_engine",
                "CoachingEngine",
                "observation_extractor",
                "ObservationExtractor",
            }
        ]
        assert service_leaked == [], (
            f"ARC-01/AR-13 compute-in-projection in {relative}: {service_leaked}"
        )


class TestCategoryASurfaceConfinement:
    """CAT-01/02/08/09 / AR-20 — EPIC-09 stays Category A harness/infra-only."""

    def test_epic09_production_touch_is_infra_observability_only(self) -> None:
        """Only authorized production file for EPIC-09 emit helper."""
        for relative in EPIC09_INFRA_FILES:
            assert (REPO_ROOT / relative).is_file(), relative

    def test_question_cycle_logging_has_no_domain_contracts(self) -> None:
        source = _read("infrastructure/observability/question_cycle_logging.py")
        imported = _imported_names(source)
        assert "domain" not in imported
        assert not any(name.startswith("domain.") for name in imported)

    def test_no_new_domain_metrics_contracts_package(self) -> None:
        for relative in (
            "domain/contracts/performance",
            "domain/contracts/metrics",
        ):
            path = REPO_ROOT / relative
            assert not path.exists(), f"CAT-08/AR-20 forbidden package: {relative}"
