# app/ui/presenters/result_presenter.py

from dataclasses import dataclass
from typing import List, Optional
import re

from domain.contracts.interview_state import InterviewState
from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.test_execution_result import TestStatus, TestType
from domain.contracts.ai_hint import AIHintInput

from services.ai_hint_engine.ai_hint_service import AIHintService
from services.execution_analysis.execution_analyzer import ExecutionAnalyzer


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

    def __init__(self):
        self._analyzer = ExecutionAnalyzer()

    def present(
        self,
        state: InterviewState,
        result: QuestionResult,
        question_text: str,
    ) -> ResultViewModel:

        evaluation = result.evaluation
        execution = result.execution

        execution_vm = self._map_execution_results([execution] if execution else [])
        errors = self._extract_errors(execution_vm)

        feedback_md = self._build_feedback_markdown(
            state,
            result,
            evaluation,
            execution,
            execution_vm,
            errors,
            question_text,
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
    # MARKDOWN
    # =========================================================

    def _build_feedback_markdown(
        self,
        state: InterviewState,
        result: QuestionResult,
        evaluation: Optional[QuestionEvaluation],
        execution: Optional[ExecutionResult],
        execution_results: List[ExecutionResultView],
        errors: List[str],
        question_text: str,
    ) -> str:

        lines: List[str] = []

        user_code = state.last_answer.content if state.last_answer else ""

        analysis = self._analyzer.analyze(execution) if execution else None

        # =========================================================
        # WRITTEN EVALUATION 
        # =========================================================

        if evaluation and not execution:

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

            return "\n".join(lines)

        # =========================================================
        # RUNTIME ERROR
        # =========================================================

        if analysis and analysis.has_runtime_error:

            clean_error = self._extract_clean_error(analysis.primary_error)

            # quick hint
            fast_hint = self._generate_runtime_hint(clean_error)

            # ai hint
            ai_hint = None
            if user_code:
                ai_hint = self._generate_ai_hint(
                    error=clean_error,
                    user_code=user_code,
                    failed_tests=[],
                    question=question_text,
                )

            lines.append("## ⚠️ Runtime Error\n")
            lines.append("Your code failed during execution.\n")

            lines.append("### Error")
            lines.append(f"`{clean_error}`\n")

            if fast_hint:
                lines.append("### 💡 Quick Hint")
                lines.append(fast_hint + "\n")

            if ai_hint:
                lines.append("### 🤖 AI Hint")
                lines.append(f"**Explanation:** {ai_hint.explanation}")
                lines.append("")
                lines.append(f"**Suggestion:** {ai_hint.suggestion}")
                lines.append("")

            return "\n".join(lines)

        # =========================================================
        # EXECUTION SUMMARY
        # =========================================================

        if execution_results:

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
        # FAILED TEST DETAILS
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

            # FILTER runtime errors (already handled above)
            failed_tests = [t for t in failed_tests if t.status != TestStatus.ERROR]

            if failed_tests:

                lines.append("### Failed Tests Details")

                for test in failed_tests:

                    label = "Hidden Test" if test.type == TestType.HIDDEN else "Test"

                    lines.append(f"**❌ {label} {test.id} — LOGIC ERROR**")

                    input_str = self._format_input(test.args, test.kwargs)
                    lines.append(f"- Input: `{input_str}`")

                    lines.append(f"- Expected: `{repr(test.expected)}`")
                    lines.append(f"- Actual: `{repr(test.actual)}`")
                    lines.append("")

                # AI hint (only logic)
                if user_code:
                    ai_hint = self._generate_ai_hint(
                        error=None,
                        user_code=user_code,
                        failed_tests=[
                            {
                                "input": t.args,
                                "expected": t.expected,
                                "actual": t.actual,
                            }
                            for t in failed_tests[:2]
                        ],
                        question=question_text,
                    )

                    if ai_hint:
                        lines.append("### 🤖 AI Hint")
                        lines.append(f"**Explanation:** {ai_hint.explanation}")
                        lines.append("")
                        lines.append(f"**Suggestion:** {ai_hint.suggestion}")
                        lines.append("")

        return "\n".join(lines)


    # =========================================================
    # HELPERS
    # =========================================================

    def _generate_ai_hint(self, error, user_code, failed_tests, question):

        try:
            service = AIHintService()

            input_data = AIHintInput(
                error=error,
                user_code=user_code[:1000],
                failed_tests=failed_tests[:2],
                question=question,
            )

            return service.generate_hint(input_data)

        except Exception:
            return None

    def _map_execution_results(self, results):
        return [
            ExecutionResultView(
                status=r.status.value,
                success=r.success,
                output=r.output,
                error=r.error,
                passed_tests=r.passed_tests,
                total_tests=r.total_tests,
                execution_time_ms=r.execution_time_ms,
            )
            for r in results
        ]

    def _extract_errors(self, execution_results):
        return [r.error for r in execution_results if r.error]

    def _format_input(self, args, kwargs):
        if args and kwargs:
            return f"args={args}, kwargs={kwargs}"
        if args:
            return str(args)
        if kwargs:
            return str(kwargs)
        return "None"

    def _extract_clean_error(self, error: Optional[str]) -> str:
        if not error:
            return ""
        lines = error.strip().splitlines()
        return lines[-1] if lines else error

    def _generate_runtime_hint(self, error: str) -> str:

        match = re.search(r"NameError: name '(.+?)' is not defined", error)
        if match:
            missing = match.group(1)
            return f"'{missing}' is not defined. You may have forgotten to import it."

        if "TypeError" in error:
            return "Check function arguments and types."

        if "IndexError" in error:
            return "Index out of range."

        if "KeyError" in error:
            return "Missing dictionary key."

        return ""
