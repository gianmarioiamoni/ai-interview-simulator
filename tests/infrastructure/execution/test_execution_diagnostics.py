# tests/infrastructure/execution/test_execution_diagnostics.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_diagnostics import (
    ExecutionDiagnostics,
    RuntimeDiagnostic,
    DiagnosticSeverity,
)


class TestDiagnosticSeverityValues:
    def test_all_values(self):
        values = {s.value for s in DiagnosticSeverity}
        assert values == {"error", "warning", "info"}


class TestRuntimeDiagnosticConstruction:
    def test_minimal_error(self):
        d = RuntimeDiagnostic(
            severity=DiagnosticSeverity.ERROR,
            error_type="SyntaxError",
            message="unexpected token",
        )
        assert d.severity == DiagnosticSeverity.ERROR
        assert d.error_type == "SyntaxError"
        assert d.line is None
        assert d.column is None
        assert d.source_snippet is None

    def test_with_position(self):
        d = RuntimeDiagnostic(
            severity=DiagnosticSeverity.ERROR,
            error_type="NameError",
            message="name 'x' is not defined",
            line=10,
            column=4,
        )
        assert d.line == 10
        assert d.column == 4

    def test_with_source_snippet(self):
        d = RuntimeDiagnostic(
            severity=DiagnosticSeverity.ERROR,
            error_type="TypeError",
            message="unsupported operand",
            source_snippet="x = 1 + '2'",
        )
        assert d.source_snippet == "x = 1 + '2'"

    def test_empty_error_type_rejected(self):
        with pytest.raises(ValidationError):
            RuntimeDiagnostic(
                severity=DiagnosticSeverity.ERROR,
                error_type="",
                message="some message",
            )

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError):
            RuntimeDiagnostic(
                severity=DiagnosticSeverity.ERROR,
                error_type="SyntaxError",
                message="",
            )

    def test_line_zero_rejected(self):
        with pytest.raises(ValidationError):
            RuntimeDiagnostic(
                severity=DiagnosticSeverity.ERROR,
                error_type="SyntaxError",
                message="err",
                line=0,
            )

    def test_column_zero_rejected(self):
        with pytest.raises(ValidationError):
            RuntimeDiagnostic(
                severity=DiagnosticSeverity.ERROR,
                error_type="SyntaxError",
                message="err",
                column=0,
            )

    def test_frozen(self, error_diagnostic):
        with pytest.raises(ValidationError):
            error_diagnostic.message = "changed"


class TestExecutionDiagnosticsEmpty:
    def test_empty_by_default(self):
        d = ExecutionDiagnostics()
        assert d.entries == []
        assert d.has_errors is False
        assert d.error_count == 0
        assert d.first_error is None

    def test_empty_errors_list(self):
        d = ExecutionDiagnostics()
        assert d.errors == []
        assert d.warnings == []
        assert d.infos == []


class TestExecutionDiagnosticsWithEntries:
    def test_error_detected(self, error_diagnostic):
        d = ExecutionDiagnostics(entries=[error_diagnostic])
        assert d.has_errors is True
        assert d.error_count == 1

    def test_first_error_returned(self, error_diagnostic):
        d = ExecutionDiagnostics(entries=[error_diagnostic])
        assert d.first_error == error_diagnostic

    def test_warning_not_counted_as_error(self, warning_diagnostic):
        d = ExecutionDiagnostics(entries=[warning_diagnostic])
        assert d.has_errors is False
        assert d.error_count == 0
        assert d.first_error is None

    def test_mixed_severity_filtering(self, error_diagnostic, warning_diagnostic):
        info = RuntimeDiagnostic(
            severity=DiagnosticSeverity.INFO,
            error_type="Info",
            message="compilation started",
        )
        d = ExecutionDiagnostics(entries=[error_diagnostic, warning_diagnostic, info])
        assert len(d.errors) == 1
        assert len(d.warnings) == 1
        assert len(d.infos) == 1

    def test_multiple_errors_counted(self, error_diagnostic):
        d = ExecutionDiagnostics(entries=[error_diagnostic, error_diagnostic])
        assert d.error_count == 2

    def test_first_error_is_first_in_list(self):
        first = RuntimeDiagnostic(
            severity=DiagnosticSeverity.ERROR,
            error_type="SyntaxError",
            message="first",
        )
        second = RuntimeDiagnostic(
            severity=DiagnosticSeverity.ERROR,
            error_type="NameError",
            message="second",
        )
        d = ExecutionDiagnostics(entries=[first, second])
        assert d.first_error == first


class TestExecutionDiagnosticsSerialization:
    def test_round_trip(self, error_diagnostic, warning_diagnostic):
        d = ExecutionDiagnostics(entries=[error_diagnostic, warning_diagnostic])
        restored = ExecutionDiagnostics.model_validate(d.model_dump())
        assert restored == d

    def test_frozen(self, error_diagnostic):
        d = ExecutionDiagnostics(entries=[error_diagnostic])
        with pytest.raises(ValidationError):
            d.entries = []
