# app/ui/presenters/evaluation_presenter.py

from dataclasses import dataclass
from typing import List, Optional

from domain.contracts.evaluation_decision import EvaluationDecision
from domain.contracts.execution_result import ExecutionResult


# =========================
# View Models (UI layer)
# =========================

@dataclass
class ExecutionResultView:
    status: str
    success: bool
    output: str
    error: Optional[str]
    passed_tests: int
    total_tests: int
    execution_time_ms: int


@dataclass
class EvaluationViewModel:
    score: float
    feedback_markdown: str
    execution_results: List[ExecutionResultView]
    errors: List[str]
    clarification_needed: bool
    follow_up_question: Optional[str]


# =========================
# Presenter
# =========================

class EvaluationPresenter:
  
    # Transform:
    # - EvaluationDecision (LLM)
    # - ExecutionResult (engine)
    # into a ViewModel UI-ready.
    # No dependency on Gradio.

    def present(
        self,
        decision: EvaluationDecision,
        execution_results: Optional[List[ExecutionResult]] = None,
    ) -> EvaluationViewModel:

        execution_vm = self._map_execution_results(execution_results or [])
        errors = self._extract_errors(execution_vm)
        feedback_md = self._build_feedback_markdown(
            decision,
            execution_vm,
            errors,
        )

        return EvaluationViewModel(
            score=decision.score,
            feedback_markdown=feedback_md,
            execution_results=execution_vm,
            errors=errors,
            clarification_needed=decision.clarification_needed,
            follow_up_question=decision.follow_up_question,
        )

    # =========================
    # Mapping
    # =========================

    def _map_execution_results(
        self,
        results: List[ExecutionResult],
    ) -> List[ExecutionResultView]:

        return [
            ExecutionResultView(
                status=result.status.value,
                success=result.success,
                output=result.output,
                error=result.error,
                passed_tests=result.passed_tests,
                total_tests=result.total_tests,
                execution_time_ms=result.execution_time_ms,
            )
            for result in results
        ]

    def _extract_errors(
        self,
        execution_results: List[ExecutionResultView],
    ) -> List[str]:

        errors: List[str] = []

        for r in execution_results:
            if r.error:
                errors.append(r.error)

        return errors

    # =========================
    # Markdown builder
    # =========================

    def _build_feedback_markdown(
        self,
        decision: EvaluationDecision,
        execution_results: List[ExecutionResultView],
        errors: List[str],
    ) -> str:

        lines: List[str] = []

        # Score
        lines.append(f"## Score: {decision.score:.1f}/100")
        lines.append("")

        # Feedback LLM
        lines.append("### Feedback")
        lines.append(decision.feedback)
        lines.append("")

        # Execution results
        if execution_results:
            lines.append("### Execution Results")

            for idx, r in enumerate(execution_results, start=1):
                status_icon = "✅" if r.success else "❌"
                lines.append(f"**Test {idx}: {status_icon} {r.status}**")

                if r.total_tests > 0:
                    lines.append(f"- Tests: {r.passed_tests}/{r.total_tests} passed")

                if r.output:
                    lines.append(f"- Output: `{r.output}`")

                if r.error:
                    lines.append(f"- Error: `{r.error}`")

                lines.append(f"- Time: {r.execution_time_ms} ms")
                lines.append("")

        # Aggregated errors
        if errors:
            lines.append("### Errors")
            for e in errors:
                lines.append(f"- {e}")
            lines.append("")

        # Follow-up (important for UX)
        if decision.clarification_needed and decision.follow_up_question:
            lines.append("### Follow-up Question")
            lines.append(decision.follow_up_question)
            lines.append("")

        return "\n".join(lines)
