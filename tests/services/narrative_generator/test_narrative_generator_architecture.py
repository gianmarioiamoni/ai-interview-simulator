# tests/services/narrative_generator/test_narrative_generator_architecture.py
# Architecture compliance tests — ADR-023, SRP, no forbidden dependencies

from __future__ import annotations

import ast
import pathlib

import pytest

_SERVICE_ROOT = pathlib.Path(__file__).parents[3] / "services" / "narrative_generator"
_GENERATOR_FILE = _SERVICE_ROOT / "narrative_generator.py"

_FORBIDDEN_IMPORTS = [
    "openai",
    "services.prompt_builders",
    "app.prompts",
    "domain.contracts.observation.observation_store",
    "services.feature_engine",
    "domain.observation",
    "services.knowledge_pipeline",
    "services.narrative_service",
    "services.interview_evaluation",
]


def _get_import_names(source: str) -> list[str]:
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


class TestArchitectureCompliance:
    def test_narrative_generator_file_exists(self) -> None:
        assert _GENERATOR_FILE.exists()

    def test_no_openai_import(self) -> None:
        source = _GENERATOR_FILE.read_text()
        assert "openai" not in source

    def test_no_prompt_loader(self) -> None:
        source = _GENERATOR_FILE.read_text()
        names = _get_import_names(source)
        assert not any("prompt_loader" in n.lower() for n in names)
        assert not any("PromptLoader" in n for n in names)

    def test_no_prompt_templates(self) -> None:
        source = _GENERATOR_FILE.read_text()
        names = _get_import_names(source)
        assert not any(n.startswith("app.prompts") for n in names)

    def test_no_observation_store_access(self) -> None:
        source = _GENERATOR_FILE.read_text()
        names = _get_import_names(source)
        assert not any("observation_store" in n.lower() for n in names)

    def test_no_feature_engine_internals(self) -> None:
        source = _GENERATOR_FILE.read_text()
        names = _get_import_names(source)
        assert not any("services.feature_engine" in n for n in names)

    def test_no_replay(self) -> None:
        source = _GENERATOR_FILE.read_text()
        names = _get_import_names(source)
        assert not any("replay" in n.lower() for n in names)

    def test_no_persistence(self) -> None:
        source = _GENERATOR_FILE.read_text()
        names = _get_import_names(source)
        assert not any("persist" in n.lower() for n in names)
        assert not any("database" in n.lower() for n in names)
        assert not any("repository" in n.lower() for n in names)

    def test_no_forbidden_imports(self) -> None:
        source = _GENERATOR_FILE.read_text()
        names = _get_import_names(source)
        for forbidden in _FORBIDDEN_IMPORTS:
            for name in names:
                assert not name.startswith(forbidden), (
                    f"Forbidden import found: '{name}' matches '{forbidden}'"
                )

    def test_narrative_builder_is_sole_narrative_creator(self) -> None:
        source = _GENERATOR_FILE.read_text()
        assert "NarrativeBuilder" in source
        assert "Narrative(" not in source.replace("NarrativeBuilder", "")

    def test_context_does_not_mutate_profile(self) -> None:
        source = (_SERVICE_ROOT / "narrative_generation_context.py").read_text()
        assert "frozen" in source

    def test_result_is_immutable(self) -> None:
        source = (_SERVICE_ROOT / "narrative_generation_result.py").read_text()
        assert "frozen" in source

    def test_metrics_is_immutable(self) -> None:
        source = (_SERVICE_ROOT / "narrative_generation_metrics.py").read_text()
        assert "frozen" in source

    def test_diagnostics_is_immutable(self) -> None:
        source = (_SERVICE_ROOT / "narrative_generation_diagnostics.py").read_text()
        assert "frozen" in source

    def test_all_five_service_files_present(self) -> None:
        expected = {
            "narrative_generator.py",
            "narrative_generation_context.py",
            "narrative_generation_result.py",
            "narrative_generation_metrics.py",
            "narrative_generation_diagnostics.py",
            "__init__.py",
        }
        actual = {f.name for f in _SERVICE_ROOT.iterdir() if f.suffix == ".py"}
        assert expected.issubset(actual)
