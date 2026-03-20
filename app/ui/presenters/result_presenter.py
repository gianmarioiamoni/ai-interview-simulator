# app/ui/presenters/result_presenter.py

from dataclasses import dataclass
from typing import List, Optional
import re

from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult, ExecutionStatus
from domain.contracts.test_execution_result import TestStatus, TestType
from domain.contracts.ai_hint import AIHintInput

from services.ai_hint_engine.ai_hint_service import AIHintService


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
            result,
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
        result: QuestionResult,
        evaluation: Optional[QuestionEvaluation],
        execution: Optional[ExecutionResult],
        execution_results: List[ExecutionResultView],
        errors: List[str],
    ) -> str:

        lines: List[str] = []

        # =========================================================
        # 🔥 RUNTIME ERROR
        # =========================================================

        if execution and execution.status == ExecutionStatus.RUNTIME_ERROR:

            clean_error = self._extract_clean_error(execution.error)
            fast_hint = self._generate_runtime_hint(clean_error)

            ai_hint = None
            if result.answer:
                ai_hint = self._generate_ai_hint(
                    error=clean_error,
                    user_code=result.answer.content,
                    failed_tests=[],
                )

            lines.append("## ⚠️ Runtime Error\n")
            lines.append("Your code failed before running any tests.\n")

            lines.append("### Error")
            lines.append(f"`{clean_error}`\n")

            if fast_hint:
                lines.append("### 💡 Hint")
                lines.append(fast_hint + "\n")

            if ai_hint:
                lines.append("### 🤖 AI Hint")
                lines.append(f"**Explanation:** {ai_hint.explanation}")
                lines.append("")
                lines.append(f"**Suggestion:** {ai_hint.suggestion}")
                lines.append("")

            return "\n".join(lines)

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
                    lines.append(f"- Error: `{self._extract_clean_error(r.error)}`")

                lines.append("")

        # =========================================================
        # 🔥 FAILED TESTS + AI HINT
        # =========================================================

        if execution and execution.test_results:

            failed_tests = [
                t
                for t in execution.test_results
                if t.type == TestType.VISIBLE and t.status != TestStatus.PASSED
            ]

            if not failed_tests:
                failed_tests = [
                    t for t in execution.test_results if t.status != TestStatus.PASSED
                ]

            if failed_tests:

                lines.append("### Failed Tests Details")

                for test in failed_tests:

                    label = "Hidden Test" if test.type == TestType.HIDDEN else "Test"

                    if test.status == TestStatus.ERROR:
                        lines.append(f"**⚠️ {label} {test.id} — RUNTIME ERROR**")
                    elif test.status == TestStatus.FAILED:
                        lines.append(f"**❌ {label} {test.id} — LOGIC ERROR**")
                    else:
                        lines.append(f"**❌ {label} {test.id} — TEST FAILED**")

                    input_str = self._format_input(test.args, test.kwargs)
                    lines.append(f"- Input: `{input_str}`")

                    if test.status == TestStatus.ERROR:
                        lines.append(f"- Error: `{test.error}`")
                        lines.append("")
                        continue

                    lines.append(f"- Expected: `{repr(test.expected)}`")
                    lines.append(f"- Actual: `{repr(test.actual)}`")
                    lines.append("")

                # 🔥 AI HINT

                ai_hint = None

                if result.answer:
                    ai_hint = self._generate_ai_hint(
                        error=None,
                        user_code=result.answer.content,
                        failed_tests=[
                            {
                                "input": t.args,
                                "expected": t.expected,
                                "actual": t.actual,
                            }
                            for t in failed_tests[:2]
                        ],
                    )

                if ai_hint:
                    lines.append("### 🤖 AI Hint")
                    lines.append(f"**Explanation:** {ai_hint.explanation}")
                    lines.append("")
                    lines.append(f"**Suggestion:** {ai_hint.suggestion}")
                    lines.append("")

        # ---------------- ERRORS ----------------

        if errors and not (execution and execution.test_results):
            lines.append("### Errors")
            for e in errors:
                lines.append(f"- {self._extract_clean_error(e)}")
            lines.append("")

        return "\n".join(lines)

    # =========================================================
    # HELPERS
    # =========================================================

    def _generate_ai_hint(self, error, user_code, failed_tests):

        try:
            service = AIHintService()

            input_data = AIHintInput(
                error=error,
                user_code=user_code[:1000],
                failed_tests=failed_tests[:2],
            )

            return service.generate_hint(input_data)

        except Exception:
            return None

    # ---------------------------------------------------------

    def _format_input(self, args, kwargs) -> str:

        if args and kwargs:
            return f"args={args}, kwargs={kwargs}"

        if args:
            return str(args)

        if kwargs:
            return str(kwargs)

        return "None"

    # ---------------------------------------------------------

    def _extract_clean_error(self, error: Optional[str]) -> str:

        if not error:
            return ""

        lines = error.strip().splitlines()

        if not lines:
            return error

        return lines[-1]

    # ---------------------------------------------------------

    def _generate_runtime_hint(self, error: str) -> str:

        match = re.search(r"NameError: name '(.+?)' is not defined", error)
        if match:
            missing = match.group(1)
            return (
                f"'{missing}' is not defined. "
                f"You may have forgotten to import it or define it."
            )

        if "TypeError" in error:
            return "Check function arguments, types, and return values."

        if "IndexError" in error:
            return "You may be accessing an index that does not exist."

        if "KeyError" in error:
            return "You are accessing a key that does not exist in a dictionary."

        return ""
