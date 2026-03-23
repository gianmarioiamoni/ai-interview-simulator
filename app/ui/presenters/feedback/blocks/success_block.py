# app/ui/presenters/feedback/blocks/success_block.py


class SuccessBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return bool(execution and execution.success)

    def build(self, state, result, evaluation, execution, analysis) -> str:

        lines = ["## ✅ All tests passed\n"]

        if execution.total_tests:
            lines.append(
                f"Passed {execution.passed_tests} / {execution.total_tests} tests\n"
            )
        else:
            lines.append("Execution completed successfully\n")

        return "\n".join(lines)
