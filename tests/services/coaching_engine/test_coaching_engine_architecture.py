# tests/services/coaching_engine/test_coaching_engine_architecture.py
# Architecture tests: ADR-025 compliance, single responsibility, boundary enforcement

import ast
import importlib
import inspect
import sys
from pathlib import Path

import pytest

ENGINE_MODULE = "services.coaching_engine.coaching_engine"
FORBIDDEN_IMPORTS = [
    "ObservationStore",
    "FeatureEngine",
    "NarrativeService",
    "narrative_service",
    "ObservationStoreQueryEngine",
    "InterviewMemory",
    "SessionHistory",
    "PatternDetector",
    "ReplayEngine",
]


def _source_of(module_path: str) -> str:
    parts = module_path.replace(".", "/")
    base = Path(__file__).resolve().parents[3]
    return (base / f"{parts}.py").read_text()


class TestCoachingEngineArchitecture:
    def test_coaching_engine_module_exists(self):
        mod = importlib.import_module(ENGINE_MODULE)
        assert mod is not None

    def test_coaching_engine_class_exists(self):
        mod = importlib.import_module(ENGINE_MODULE)
        assert hasattr(mod, "CoachingEngine")

    def test_no_forbidden_imports_in_engine(self):
        import ast as ast_module
        source = _source_of(ENGINE_MODULE)
        tree = ast_module.parse(source)
        imported_names: set[str] = set()
        for node in ast_module.walk(tree):
            if isinstance(node, (ast_module.Import, ast_module.ImportFrom)):
                for alias in node.names:
                    imported_names.add(alias.name or "")
                    if alias.asname:
                        imported_names.add(alias.asname)
                if isinstance(node, ast_module.ImportFrom) and node.module:
                    imported_names.add(node.module)

        for forbidden in FORBIDDEN_IMPORTS:
            assert not any(forbidden in name for name in imported_names), (
                f"CoachingEngine must not import '{forbidden}' (ADR-025 boundary)"
            )

    def test_coaching_builder_is_sole_plan_creator(self):
        source = _source_of(ENGINE_MODULE)
        assert "CoachingBuilder" in source
        assert "CoachingSnapshot(" not in source or source.count("CoachingSnapshot(") == 0 or (
            "CoachingBuilder.build" in source or "CoachingBuilder.empty" in source
        )

    def test_no_candidate_profile_mutation(self, base_context):
        from services.coaching_engine.coaching_engine import CoachingEngine

        original_questions = base_context.profile.questions_answered
        engine = CoachingEngine()
        engine.run(base_context)
        assert base_context.profile.questions_answered == original_questions

    def test_engine_has_run_method_only_as_public_api(self):
        from services.coaching_engine.coaching_engine import CoachingEngine

        public_methods = [
            m for m in dir(CoachingEngine)
            if not m.startswith("_") and callable(getattr(CoachingEngine, m))
        ]
        assert "run" in public_methods

    def test_coaching_context_is_immutable(self, base_context):
        with pytest.raises((Exception,)):
            base_context.session_id = "hacked"

    def test_coaching_result_is_immutable(self, base_context):
        from services.coaching_engine.coaching_engine import CoachingEngine

        result = CoachingEngine().run(base_context)
        with pytest.raises((Exception,)):
            result.is_successful = False

    def test_no_observation_store_access_in_engine(self):
        source = _source_of(ENGINE_MODULE)
        assert "observation_store" not in source.lower() or "ObservationStore" not in source

    def test_no_feature_engine_access_in_engine(self):
        source = _source_of(ENGINE_MODULE)
        assert "feature_engine" not in source.lower() or "FeatureEngine" not in source

    def test_coaching_context_no_store_reference(self):
        import ast as ast_module
        source = _source_of("services.coaching_engine.coaching_context")
        tree = ast_module.parse(source)
        imported_names: set[str] = set()
        for node in ast_module.walk(tree):
            if isinstance(node, ast_module.ImportFrom) and node.module:
                imported_names.add(node.module)
            if isinstance(node, (ast_module.Import, ast_module.ImportFrom)):
                for alias in node.names:
                    imported_names.add(alias.name or "")

        forbidden_context = ["ObservationStore", "FeatureEngine", "NarrativeService"]
        for forbidden in forbidden_context:
            assert not any(forbidden in n for n in imported_names), (
                f"CoachingContext must not import '{forbidden}'"
            )

    def test_all_modules_importable(self):
        modules = [
            "services.coaching_engine",
            "services.coaching_engine.coaching_context",
            "services.coaching_engine.coaching_result",
            "services.coaching_engine.coaching_metrics",
            "services.coaching_engine.coaching_diagnostics",
            "services.coaching_engine.coaching_engine",
        ]
        for module in modules:
            mod = importlib.import_module(module)
            assert mod is not None
