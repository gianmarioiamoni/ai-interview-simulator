# app/ui/presenters/feedback/blocks/runtime_error_block.py

from typing import Optional

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)
from domain.contracts.feedback.severity import Severity
from domain.contracts.feedback.error_type import ErrorType
from infrastructure.config.evaluation import FEEDBACK_CONFIDENCE_RUNTIME_ERROR

_MAX_TRACEBACK_LINES = 15


def _format_traceback(raw: str) -> str:
    lines = raw.strip().splitlines()
    if len(lines) > _MAX_TRACEBACK_LINES:
        kept = lines[:2] + ["  ..."] + lines[-(  _MAX_TRACEBACK_LINES - 3):]
        lines = kept
    return "\n".join(lines)


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
        self, _state, _result, _evaluation, execution, analysis, _quality
    ) -> FeedbackBlockResult:

        raw_error = (analysis.primary_error or "").strip()
        error_type = analysis.error_type

        # -----------------------------------------------------
        # TYPE-AWARE MESSAGING
        # -----------------------------------------------------

        if error_type == ErrorType.SYNTAX:
            title = "⚠️ Syntax Error"
            suggestion = "Check syntax (missing colons, parentheses, indentation)"

        elif error_type == ErrorType.SIGNATURE:
            title = "⚠️ Signature Error"
            suggestion = "Ensure function signature matches expected parameters"

        elif error_type == ErrorType.TIMEOUT:
            title = "⚠️ Timeout Error"
            suggestion = "Optimize algorithm (likely O(n²) or worse)"

        elif error_type == ErrorType.RUNTIME:
            title = "⚠️ Runtime Error"
            suggestion = "Check variable definitions, imports, and edge cases"

        else:
            title = "⚠️ Runtime Error"
            suggestion = "Check variable definitions, imports, and variable scope"

        # -----------------------------------------------------
        # SIGNALS  (last line = exception summary for signal)
        # -----------------------------------------------------

        last_line = raw_error.splitlines()[-1] if raw_error else raw_error

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=last_line,
            )
        ]

        # -----------------------------------------------------
        # LEARNING
        # -----------------------------------------------------

        learning = [
            LearningSuggestion(
                topic="Debugging",
                action=suggestion,
            )
        ]

        # -----------------------------------------------------
        # CONTENT — full traceback + optional failing input
        # -----------------------------------------------------

        traceback_section = _format_traceback(raw_error)
        failing_input = _extract_failing_input(execution)

        parts: list[str] = []
        if failing_input is not None:
            parts.append(f"**Input:** `{failing_input}`\n")
        parts.append(f"**Traceback:**\n```\n{traceback_section}\n```")

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
