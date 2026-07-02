# tests/services/knowledge_pipeline/test_knowledge_pipeline_architecture.py
# Architecture tests: no forbidden concepts, correct ownership boundaries

from __future__ import annotations

import ast
import pathlib

import pytest

PIPELINE_ROOT = pathlib.Path(__file__).parents[3] / "services" / "knowledge_pipeline"

FORBIDDEN_IMPORTS = {
    "Narrative",
    "CoachingAction",
    "Replay",
    "SessionHistory",
    "Persistence",
    "LanguageExecutor",
    "Calibration",
    "LLM",
    "openai",
    "anthropic",
}

PIPELINE_FILES = list(PIPELINE_ROOT.glob("*.py"))


def _imported_names(filepath: pathlib.Path) -> set[str]:
    """Return all names referenced in import statements in a source file."""
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


class TestNoBannedImports:
    @pytest.mark.parametrize("filepath", PIPELINE_FILES, ids=lambda f: f.name)
    def test_no_forbidden_imports(self, filepath: pathlib.Path) -> None:
        imported = _imported_names(filepath)
        for name in FORBIDDEN_IMPORTS:
            assert name not in imported, (
                f"Forbidden import '{name}' found in {filepath.name}"
            )


class TestNoBizLogicInOrchestrator:
    def test_pipeline_does_not_define_business_logic_classes(self):
        """KnowledgePipeline must not define new domain classes."""
        pipeline_file = PIPELINE_ROOT / "knowledge_pipeline.py"
        source = pipeline_file.read_text()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        # Only KnowledgePipeline itself is allowed — no domain model definitions
        assert class_names == ["KnowledgePipeline"], (
            f"Unexpected class definitions in knowledge_pipeline.py: {class_names}"
        )


class TestCandidateProfileContractUniqueness:
    def test_no_duplicate_candidate_profile_definition(self):
        """Only domain/contracts/reasoning/candidate_profile.py defines CandidateProfile class."""
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
                if isinstance(node, ast.ClassDef) and node.name == "CandidateProfile":
                    definitions.append(str(f.relative_to(project_root)))

        assert len(definitions) == 1, (
            f"Multiple CandidateProfile class definitions found: {definitions}"
        )
        assert "domain/contracts/reasoning/candidate_profile.py" in definitions[0]


class TestPipelineOwnsOrchestrationOnly:
    def test_pipeline_run_delegates_to_components(self):
        """KnowledgePipeline.run() must call extractor, store, feature_engine, builder."""
        pipeline_file = PIPELINE_ROOT / "knowledge_pipeline.py"
        source = pipeline_file.read_text()
        # All delegation calls must be present
        assert "self._extractor.extract(" in source
        assert "self._store.snapshot(" in source
        assert "self._feature_engine.run(" in source
        assert "CandidateProfileBuilder" in source

    def test_pipeline_does_not_compute_knowledge(self):
        """Pipeline must not contain domain computation keywords."""
        pipeline_file = PIPELINE_ROOT / "knowledge_pipeline.py"
        source = pipeline_file.read_text()
        forbidden_ops = ["ProfileDimension", "DimensionTrace", "ProfileSignal"]
        for op in forbidden_ops:
            assert op not in source, f"Pipeline should not reference domain type '{op}'"
