# app/ui/presenters/result_presenter.py

from dataclasses import dataclass
from typing import List, Optional

from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.test_execution_result import TestStatus, TestType


# =========================================================
# VIEW MODELS
# =========================================================


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
class ResultViewModel:
    score: float
    feedback_markdown: str
    execution_results: List[ExecutionResultView]
    errors: List[str]
    passed: bool


# =========================================================
# PRESENTER
# =========================================================


class ResultPresenter:

    def present(self, result: QuestionResult) -> ResultViewModel:

        evaluation = result.evaluation
        execution = result.execution

        execution_vm = self._map_execution_results([execution] if execution else [])

        errors = self._extract_errors(execution_vm)

        feedback_md = self._build_feedback_markdown(
            evaluation,
            execution,
            execution_vm,
            errors,
        )

        score = evaluation.score if evaluation else 0
        passed = evaluation.passed if evaluation else False

        return ResultViewModel(
            score=score,
            feedback_markdown=feedback_md,
            execution_results=execution_vm,
            errors=errors,
            passed=passed,
        )

    # =========================================================
    # MAPPING
    # =========================================================

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

    # =========================================================
    # MARKDOWN
    # =========================================================

    def _build_feedback_markdown(
        self,
        evaluation: Optional[QuestionEvaluation],
        execution: Optional[ExecutionResult],
        execution_results: List[ExecutionResultView],
        errors: List[str],
    ) -> str:

        lines: List[str] = []

        # ---------------- EVALUATION ----------------
        if evaluation:

            lines.append(f"## Score: {evaluation.score:.1f}/100\n")

            lines.append("### Feedback")
            lines.append(evaluation.feedback + "\n")

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

        # ---------------- EXECUTION SUMMARY ----------------
        if execution_results:

            if not evaluation:
                lines.append("## Execution Summary\n")

            lines.append("### Execution Results")

            for idx, r in enumerate(execution_results, start=1):
                icon = "✅" if r.success else "❌"
                lines.append(f"**Run {idx}: {icon} {r.status}**")

                if r.total_tests > 0:
                    lines.append(f"- Tests: {r.passed_tests}/{r.total_tests}")

                if r.error:
                    lines.append(f"- Error: `{r.error}`")

                lines.append("")

        # =========================================================
        # 🔥 DETAILED TEST FEEDBACK
        # =========================================================

        if execution and execution.test_results:

            failed_tests = [
                t
                for t in execution.test_results
                if t.type == TestType.VISIBLE and t.status != TestStatus.PASSED
            ]

            # fallback → usa hidden se non ci sono visible
            if not failed_tests:
                failed_tests = [
                    t for t in execution.test_results if t.status != TestStatus.PASSED
                ]

            if failed_tests:

                lines.append("### Failed Tests Details")

                for test in failed_tests:

                    # 🔥 LABEL
                    label = "Hidden Test" if test.type == TestType.HIDDEN else "Test"

                    # HEADER
                    if test.status == TestStatus.ERROR:
                        lines.append(f"**⚠️ {label} {test.id} — ERROR**")
                    else:
                        lines.append(f"**❌ {label} {test.id} — FAILED**")

                    # INPUT
                    input_str = self._format_input(test.args, test.kwargs)
                    lines.append(f"- Input: `{input_str}`")

                    # ERROR
                    if test.status == TestStatus.ERROR:
                        lines.append(f"- Error: `{test.error}`")
                        lines.append("")
                        continue

                    # EXPECTED / ACTUAL
                    lines.append(f"- Expected: `{test.expected}`")
                    lines.append(f"- Actual: `{test.actual}`")
                    lines.append("")

        # ---------------- ERRORS ----------------
        if errors:
            lines.append("### Errors")
            for e in errors:
                lines.append(f"- {e}")
            lines.append("")

        return "\n".join(lines)

    # =========================================================
    # HELPERS
    # =========================================================

    def _format_input(self, args, kwargs) -> str:

        if args and kwargs:
            return f"args={args}, kwargs={kwargs}"

        if args:
            return str(args)

        if kwargs:
            return str(kwargs)

        return "None"
