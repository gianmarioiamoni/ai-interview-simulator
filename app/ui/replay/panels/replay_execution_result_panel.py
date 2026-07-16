# app/ui/replay/panels/replay_execution_result_panel.py

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.replay.replay_question_record import ReplayQuestionRecord


@dataclass(frozen=True)
class ExecutionResultViewModel:
    """C-06 rendering model (EPIC-04-DATA-MODEL §4.6)."""

    execution_status: str
    status_badge: str
    passed_tests: int
    total_tests: int
    pass_rate_pct: float


class ReplayExecutionResultPanel:
    """C-06: coding question execution result (only when is_coding_question)."""

    def __init__(self, record: ReplayQuestionRecord) -> None:
        self._record = record

    def render(self) -> ExecutionResultViewModel | None:
        """Return the view model when coding; otherwise None (I-C06-01)."""
        if not self._record.is_coding_question:
            return None

        passed = self._record.passed_tests
        total = self._record.total_tests
        status = self._record.execution_status
        if passed is None or total is None or status is None:
            raise RuntimeError("Coding question missing co-present execution fields (V-RQR-04).")

        return ExecutionResultViewModel(
            execution_status=status,
            status_badge=status.replace("_", " ").title(),
            passed_tests=passed,
            total_tests=total,
            pass_rate_pct=(passed / total) * 100.0,
        )
