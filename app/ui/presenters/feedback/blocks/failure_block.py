# app/ui/presenters/feedback/blocks/failure_block.py

from domain.contracts.test_execution_result import TestStatus


class FailureBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:

        if not execution or not execution.test_results:
            return False

        return any(
            t.status != TestStatus.PASSED and t.status != TestStatus.ERROR
            for t in execution.test_results
        )

    def build(self, state, result, evaluation, execution, analysis) -> str:

        failed = [
            t
            for t in execution.test_results
            if t.status != TestStatus.PASSED and t.status != TestStatus.ERROR
        ]

        failed_str = "\n".join(
            [
                f"Input: {t.args} | Expected: {t.expected} | Actual: {t.actual}"
                for t in failed[:2]
            ]
        )

        ai_hint = result.ai_hint if result else None

        lines = ["### Failed Tests", failed_str + "\n"]

        if ai_hint:
            lines.append("### 🤖 AI Hint")
            lines.append(f"**Explanation:** {ai_hint.explanation}")
            lines.append(f"**Suggestion:** {ai_hint.suggestion}")

        return "\n".join(lines)
