from domain.contracts.execution_result import ExecutionResult, ExecutionStatus
from domain.contracts.question_evaluation import QuestionEvaluation


class ExecutionScorePolicy:
    """
    Adjusts LLM evaluation score based on execution results.
    """

    def apply(
        self,
        evaluation: QuestionEvaluation,
        execution_result: ExecutionResult | None,
    ) -> QuestionEvaluation:

        if execution_result is None:
            return evaluation

        # ---------------------------------------------------------
        # Hard failures
        # ---------------------------------------------------------

        if execution_result.status in [
            ExecutionStatus.SYNTAX_ERROR,
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.INTERNAL_ERROR,
        ]:

            capped_score = min(evaluation.score, 30.0)

            return evaluation.model_copy(
                update={
                    "score": capped_score,
                    "feedback": evaluation.feedback
                    + "\n\n⚠ Execution failed during runtime.",
                }
            )

        # ---------------------------------------------------------
        # Failed tests
        # ---------------------------------------------------------

        if execution_result.status == ExecutionStatus.FAILED_TESTS:

            if execution_result.total_tests > 0:

                ratio = execution_result.passed_tests / execution_result.total_tests
                cap = ratio * 100

                capped_score = min(evaluation.score, cap)

                return evaluation.model_copy(
                    update={
                        "score": capped_score,
                        "feedback": evaluation.feedback
                        + f"\n\nTests passed: {execution_result.passed_tests}/{execution_result.total_tests}",
                    }
                )

        # ---------------------------------------------------------
        # Successful execution
        # ---------------------------------------------------------

        return evaluation
