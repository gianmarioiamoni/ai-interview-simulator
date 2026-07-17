# app/ui/presenters/feedback/blocks/runtime_error_block.py
# EPIC-07 P4/C8 — candidate-safe execution error block via EC-EX-01 (no traceback).

from typing import Optional

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)
from app.ui.presentation.execution_error_kind import ExecutionErrorKind
from app.ui.presentation.execution_error_presentation import project_execution_error
from app.ui.presentation.question_feedback_surface import format_execution_error_markdown
from domain.contracts.feedback.severity import Severity
from domain.contracts.feedback.error_type import ErrorType
from infrastructure.config.evaluation import FEEDBACK_CONFIDENCE_RUNTIME_ERROR

_ERROR_TYPE_TO_KIND: dict[ErrorType, ExecutionErrorKind] = {
    ErrorType.SYNTAX: ExecutionErrorKind.SYNTAX,
    ErrorType.RUNTIME: ExecutionErrorKind.RUNTIME,
    ErrorType.SIGNATURE: ExecutionErrorKind.RUNTIME,
    ErrorType.TIMEOUT: ExecutionErrorKind.RUNTIME,
    ErrorType.UNKNOWN: ExecutionErrorKind.UNKNOWN_SAFE,
}


def _extract_failing_input(execution) -> Optional[str]:
    if execution is None:
        return None
    sample = getattr(execution, "hidden_failure_sample", None)
    if sample and sample.get("args") is not None:
        return str(sample["args"])
    test_results = getattr(execution, "test_results", None) or []
    for t in test_results:
        status = getattr(t, "status", None)
        if status and status.value in ("failed", "error"):
            args = getattr(t, "args", None)
            if args is not None:
                return str(args)
    return None


def _structured_kind(error_type: ErrorType | None) -> ExecutionErrorKind | None:
    if error_type is None:
        return None
    return _ERROR_TYPE_TO_KIND.get(error_type)


class RuntimeErrorBlock:

    def can_handle(
        self,
        _result,
        _evaluation,
        _execution,
        analysis,
    ) -> bool:

        return bool(analysis and analysis.has_runtime_error)

    def build(
        self, _state, _result, evaluation, execution, analysis, _quality
    ) -> FeedbackBlockResult:

        raw_error = (analysis.primary_error or "").strip()
        error_type = analysis.error_type

        presentation = project_execution_error(
            structured_kind=_structured_kind(error_type),
            raw_error=raw_error,
        )

        if presentation.kind is ExecutionErrorKind.SYNTAX:
            title = "⚠️ Syntax Error"
            suggestion = "Check syntax (missing colons, parentheses, indentation)"
        elif error_type == ErrorType.SIGNATURE:
            title = "⚠️ Signature Error"
            suggestion = "Ensure function signature matches expected parameters"
        elif error_type == ErrorType.TIMEOUT:
            title = "⚠️ Timeout Error"
            suggestion = "Optimize algorithm (likely O(n²) or worse)"
        elif presentation.kind is ExecutionErrorKind.SQL:
            title = "⚠️ SQL Error"
            suggestion = "Check SQL syntax, table names, and join conditions"
        elif presentation.kind is ExecutionErrorKind.RUNTIME:
            title = "⚠️ Runtime Error"
            suggestion = "Check variable definitions, imports, and edge cases"
        else:
            title = "⚠️ Execution Error"
            suggestion = "Review your solution and try again"

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=presentation.candidate_message,
            )
        ]

        learning = [
            LearningSuggestion(
                topic="Debugging",
                action=suggestion,
            )
        ]

        failing_input = _extract_failing_input(execution)
        parts: list[str] = []
        if failing_input is not None:
            parts.append(f"**Input:** `{failing_input}`")
        parts.append(format_execution_error_markdown(presentation))

        if evaluation and getattr(evaluation, "feedback", None):
            parts.append(f"### 🔎 Analysis\n{evaluation.feedback}")

        content = "\n\n".join(parts)

        return FeedbackBlockResult(
            title=title,
            content=content,
            severity=Severity.ERROR,
            confidence=FEEDBACK_CONFIDENCE_RUNTIME_ERROR,
            signals=signals,
            learning=learning,
            quality=None,
        )
