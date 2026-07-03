# tests/services/interview_pipeline/test_interview_pipeline_architecture.py
# Architecture tests: no forbidden imports, no business logic in orchestrator

from __future__ import annotations

import ast
import pathlib

import pytest

PIPELINE_ROOT = pathlib.Path(__file__).parents[3] / "services" / "interview_pipeline"

PIPELINE_FILES = list(PIPELINE_ROOT.glob("*.py"))

FORBIDDEN_IMPORTS = {
    "openai",
    "anthropic",
    "PromptLoader",
    "ObservationExtractor",
    "FeatureEngine",
    "CandidateProfileBuilder",
    "LLM",
    "sqlalchemy",
    "repository",
    "persistence",
}

# Business logic symbols that must not appear inside interview_pipeline.py
FORBIDDEN_BIZ_SYMBOLS = [
    "ProfileDimension",
    "DimensionTrace",
    "NarrativeSection",
    "LearningObjective",
    "CoachingAction",
    "SessionHistoryBuilder",
    "ReplayManifest",
]


def _imported_names(filepath: pathlib.Path) -> set[str]:
    source = filepath.read_text()
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                if alias.asname:
                    names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
            for alias in node.names:
                names.add(alias.name)
                if alias.asname:
                    names.add(alias.asname)
    return names


class TestNoForbiddenImports:
    @pytest.mark.parametrize("filepath", PIPELINE_FILES, ids=lambda f: f.name)
    def test_no_forbidden_imports(self, filepath: pathlib.Path) -> None:
        imported = _imported_names(filepath)
        for name in FORBIDDEN_IMPORTS:
            assert name not in imported, (
                f"Forbidden import '{name}' found in {filepath.name}"
            )


class TestOrchestratorContainsOnlyOneClass:
    def test_interview_pipeline_defines_only_orchestrator_class(self):
        pipeline_file = PIPELINE_ROOT / "interview_pipeline.py"
        source = pipeline_file.read_text()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert class_names == ["InterviewPipeline"], (
            f"Unexpected class definitions in interview_pipeline.py: {class_names}"
        )


class TestOrchestratorDelegatesAllStages:
    def test_delegates_to_knowledge_pipeline(self):
        source = (PIPELINE_ROOT / "interview_pipeline.py").read_text()
        assert "self._knowledge_pipeline.run(" in source

    def test_delegates_to_narrative_generator(self):
        source = (PIPELINE_ROOT / "interview_pipeline.py").read_text()
        assert "self._narrative_generator.generate(" in source

    def test_delegates_to_coaching_engine(self):
        source = (PIPELINE_ROOT / "interview_pipeline.py").read_text()
        assert "self._coaching_engine.run(" in source

    def test_delegates_to_session_close_pipeline(self):
        source = (PIPELINE_ROOT / "interview_pipeline.py").read_text()
        assert "self._session_close_pipeline" in source


class TestNoBizLogicInOrchestrator:
    @pytest.mark.parametrize("symbol", FORBIDDEN_BIZ_SYMBOLS)
    def test_orchestrator_does_not_use_business_logic_symbols(self, symbol: str):
        source = (PIPELINE_ROOT / "interview_pipeline.py").read_text()
        assert symbol not in source, (
            f"Business logic symbol '{symbol}' found in interview_pipeline.py"
        )


class TestInterviewPipelineResultUniqueness:
    def test_no_duplicate_interview_pipeline_result_class(self):
        project_root = pathlib.Path(__file__).parents[3]
        py_files = list(project_root.rglob("*.py"))
        definitions = []
        for f in py_files:
            if "__pycache__" in str(f):
                continue
            try:
                source = f.read_text()
                tree = ast.parse(source)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "InterviewPipelineResult":
                    definitions.append(str(f.relative_to(project_root)))
        assert len(definitions) == 1, (
            f"Multiple InterviewPipelineResult definitions found: {definitions}"
        )
