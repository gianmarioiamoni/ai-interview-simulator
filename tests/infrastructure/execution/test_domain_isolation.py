# tests/infrastructure/execution/test_domain_isolation.py

"""
Architecture validation tests: verify that execution layer contracts
contain no Domain leakage (I-27-1 through I-27-8).

These tests inspect the source modules at import-time to ensure no
domain concepts are referenced in infrastructure/execution/contracts/.
"""

import ast
import pathlib
import pytest


CONTRACTS_DIR = pathlib.Path(
    "infrastructure/execution/contracts"
)

FORBIDDEN_DOMAIN_NAMES = {
    "CandidateProfile",
    "FeatureEngine",
    "EvidenceSignal",
    "Observation",
    "SessionHistory",
    "Narrative",
    "Coaching",
    "ObservationType",
    "ProfileFeature",
    "NarrativeGenerator",
    "CoachingEngine",
    "CoachingPlan",
}

FORBIDDEN_DOMAIN_MODULES = {
    "domain.contracts.observation",
    "domain.contracts.feature",
    "domain.contracts.candidate",
    "domain.contracts.session",
    "domain.contracts.narrative",
    "domain.contracts.coaching",
    "services.interview_reasoner",
    "services.feedback",
}


def collect_source_files() -> list[pathlib.Path]:
    return [
        p for p in CONTRACTS_DIR.rglob("*.py")
        if p.name != "__init__.py"
    ]


class TestNoForbiddenImports:
    @pytest.mark.parametrize("source_file", collect_source_files())
    def test_no_forbidden_module_imported(self, source_file: pathlib.Path):
        source = source_file.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in FORBIDDEN_DOMAIN_MODULES:
                        assert not node.module.startswith(forbidden), (
                            f"{source_file.name}: imports forbidden domain module '{node.module}'"
                        )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in FORBIDDEN_DOMAIN_MODULES:
                            assert not alias.name.startswith(forbidden), (
                                f"{source_file.name}: imports forbidden domain module '{alias.name}'"
                            )


class TestNoForbiddenDomainNames:
    @pytest.mark.parametrize("source_file", collect_source_files())
    def test_no_forbidden_domain_name_referenced(self, source_file: pathlib.Path):
        source = source_file.read_text()
        # Strip comment lines to avoid flagging docstring mentions
        non_comment_lines = [
            line for line in source.splitlines()
            if not line.lstrip().startswith("#")
        ]
        code_only = "\n".join(non_comment_lines)
        tree = ast.parse(source)
        # Check only actual identifiers in the AST, not string literals / docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in FORBIDDEN_DOMAIN_NAMES, (
                    f"{source_file.name}: references forbidden domain name '{node.id}' (I-27-1)"
                )
            elif isinstance(node, ast.Attribute):
                assert node.attr not in FORBIDDEN_DOMAIN_NAMES, (
                    f"{source_file.name}: references forbidden domain attr '{node.attr}' (I-27-1)"
                )


class TestNoEvidenceSignalReference:
    """I-27-2: LanguageExecutor never produces EvidenceSignal."""

    @pytest.mark.parametrize("source_file", collect_source_files())
    def test_no_evidence_signal(self, source_file: pathlib.Path):
        source = source_file.read_text()
        tree = ast.parse(source)
        # Check AST identifiers only (not docstrings/comments)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id != "EvidenceSignal", (
                    f"{source_file.name}: AST references EvidenceSignal (violates I-27-2)"
                )
            elif isinstance(node, ast.Attribute):
                assert node.attr != "EvidenceSignal", (
                    f"{source_file.name}: AST references EvidenceSignal attr (violates I-27-2)"
                )


class TestLanguageIndependentStatus:
    """I-27-9: ExecutionResult is language-independent in structure."""

    def test_execution_result_has_no_language_specific_fields(self):
        from infrastructure.execution.contracts.execution_result import ExecutionResult
        fields = set(ExecutionResult.model_fields.keys())
        language_specific_forbidden = {
            "python_traceback",
            "node_error",
            "ts_compiler_error",
            "jvm_error",
            "cpython_version",
            "nodejs_version",
        }
        for field in language_specific_forbidden:
            assert field not in fields, (
                f"ExecutionResult has language-specific field '{field}' (violates I-27-9)"
            )

    def test_execution_status_has_no_language_specific_values(self):
        from infrastructure.execution.contracts.execution_status import ExecutionStatus
        language_prefixes = ["python_", "javascript_", "typescript_", "java_", "go_"]
        for status in ExecutionStatus:
            for prefix in language_prefixes:
                assert not status.value.startswith(prefix), (
                    f"ExecutionStatus has language-specific value '{status.value}' (violates I-27-9)"
                )


class TestNoSandboxImplementationLeakage:
    """No sandbox implementation calls in contracts layer."""

    @pytest.mark.parametrize("source_file", collect_source_files())
    def test_no_sandbox_implementation_calls(self, source_file: pathlib.Path):
        """Check for actual executable sandbox calls, not documentation mentions."""
        source = source_file.read_text()
        tree = ast.parse(source)
        forbidden_calls = {"subprocess", "Popen", "check_call", "check_output"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_calls:
                pytest.fail(
                    f"{source_file.name}: contains sandbox call '{node.attr}' "
                    f"— contracts layer must not implement execution"
                )
            if isinstance(node, ast.Name) and node.id in forbidden_calls:
                pytest.fail(
                    f"{source_file.name}: contains sandbox name '{node.id}' "
                    f"— contracts layer must not implement execution"
                )
