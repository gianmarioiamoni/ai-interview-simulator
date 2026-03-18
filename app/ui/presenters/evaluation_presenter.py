# app/ui/presenters/evaluation_presenter.py

from dataclasses import dataclass
from typing import List, Optional

from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult


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
    passed: bool


class EvaluationPresenter:

    def present(
        self,
        evaluation: QuestionEvaluation,
        execution_results: Optional[List[ExecutionResult]] = None,
    ) -> EvaluationViewModel:

        execution_vm = self._map_execution_results(execution_results or [])
        errors = self._extract_errors(execution_vm)

        feedback_md = self._build_feedback_markdown(
            evaluation,
            execution_vm,
            errors,
        )

        return EvaluationViewModel(
            score=evaluation.score,
            feedback_markdown=feedback_md,
            execution_results=execution_vm,
            errors=errors,
            passed=evaluation.passed,
        )

    # ---------------- MAPPING ----------------

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

        return [r.error for r in execution_results if r.error]

    # ---------------- MARKDOWN ----------------

    def _build_feedback_markdown(
        self,
        evaluation: QuestionEvaluation,
        execution_results: List[ExecutionResultView],
        errors: List[str],
    ) -> str:

        lines: List[str] = []

        # Score
        lines.append(f"## Score: {evaluation.score:.1f}/100")
        lines.append("")

        # Feedback
        lines.append("### Feedback")
        lines.append(evaluation.feedback)
        lines.append("")

        # Strengths / Weaknesses (hai questi → sfruttali!)
        if evaluation.strengths:
            lines.append("### Strengths")
            for s in evaluation.strengths:
                lines.append(f"- {s}")
            lines.append("")

        if evaluation.weaknesses:
            lines.append("### Weaknesses")
            for w in evaluation.weaknesses:
                lines.append(f"- {w}")
            lines.append("")

        # Execution
        if execution_results:
            lines.append("### Execution Results")

            for idx, r in enumerate(execution_results, start=1):
                icon = "✅" if r.success else "❌"
                lines.append(f"**Test {idx}: {icon} {r.status}**")

                if r.total_tests > 0:
                    lines.append(f"- Tests: {r.passed_tests}/{r.total_tests}")

                if r.error:
                    lines.append(f"- Error: `{r.error}`")

                lines.append("")

        # Errors
        if errors:
            lines.append("### Errors")
            for e in errors:
                lines.append(f"- {e}")
            lines.append("")

        return "\n".join(lines)
