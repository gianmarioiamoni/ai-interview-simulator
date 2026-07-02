# infrastructure/execution/contracts/execution_diagnostics.py

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DiagnosticSeverity(str, Enum):
    """Severity classification for a single diagnostic entry."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuntimeDiagnostic(BaseModel):
    """A single structured diagnostic produced by the execution runtime.

    Language-independent. Concrete LanguageExecutor implementations map
    language-specific error formats to this contract before returning.

    error_type is a normalised error class name (e.g. 'SyntaxError',
    'TypeError', 'MemoryError'). message is the human-readable description.
    line and column are 1-indexed source positions (None when unavailable).
    """

    severity: DiagnosticSeverity
    error_type: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    line: Optional[int] = Field(default=None, ge=1)
    column: Optional[int] = Field(default=None, ge=1)
    source_snippet: Optional[str] = Field(default=None)

    model_config = {"frozen": True, "extra": "forbid"}


class ExecutionDiagnostics(BaseModel):
    """Aggregate container for all diagnostics from a code execution.

    Attached to ExecutionResult. Provides structured access to errors,
    warnings, and informational messages produced by the sandbox and runtime.

    Infrastructure-only. No Domain concept reads ExecutionDiagnostics directly.
    """

    entries: list[RuntimeDiagnostic] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def errors(self) -> list[RuntimeDiagnostic]:
        return [d for d in self.entries if d.severity == DiagnosticSeverity.ERROR]

    @property
    def warnings(self) -> list[RuntimeDiagnostic]:
        return [d for d in self.entries if d.severity == DiagnosticSeverity.WARNING]

    @property
    def infos(self) -> list[RuntimeDiagnostic]:
        return [d for d in self.entries if d.severity == DiagnosticSeverity.INFO]

    @property
    def has_errors(self) -> bool:
        return any(d.severity == DiagnosticSeverity.ERROR for d in self.entries)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.entries if d.severity == DiagnosticSeverity.ERROR)

    @property
    def first_error(self) -> Optional[RuntimeDiagnostic]:
        return next(
            (d for d in self.entries if d.severity == DiagnosticSeverity.ERROR), None
        )
