# app/core/evaluation/execution_score_policy.py

from domain.contracts.execution.execution_result import ExecutionResult, ExecutionStatus
from domain.contracts.question.question_evaluation import QuestionEvaluation

from services.score_calibration_service import ScoreCalibrationService


class ExecutionScorePolicy:

    def __init__(self):
        self._calibration = ScoreCalibrationService()

    # Adjusts LLM evaluation score based on execution results.

    def apply(
        self,
        evaluation: QuestionEvaluation,
        execution_result: ExecutionResult | None,
    ) -> QuestionEvaluation:

        if execution_result is None:
            return evaluation

        # Metadata propagated to QuestionEvaluation
        execution_metadata = {
            "passed_tests": execution_result.passed_tests,
            "total_tests": execution_result.total_tests,
            "execution_status": execution_result.status.value,
        }

        # ---------------------------------------------------------
        # Hard failures (syntax, runtime, timeout, internal error)
        # ---------------------------------------------------------

        if execution_result.status in [
            ExecutionStatus.SYNTAX_ERROR,
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.INTERNAL_ERROR,
        ]:

            capped_score = min(evaluation.score, 30.0)

            calibrated_score = self._calibration.calibrate(capped_score)

            return evaluation.model_copy(
                update={
                    **execution_metadata,
                    "score": calibrated_score,
                    "feedback": (
                        evaluation.feedback + "\n\n⚠ Execution failed during runtime."
                    ),
                }
            )

        # ---------------------------------------------------------
        # Failed tests
        # ---------------------------------------------------------

        if execution_result.status == ExecutionStatus.FAILED_TESTS:

            print(
                f"Execution policy applied: FAILED_TESTS "
                f"{execution_result.passed_tests}/{execution_result.total_tests}"
            )

            ratio = 0.0

            if execution_result.total_tests > 0:
                ratio = execution_result.passed_tests / execution_result.total_tests

            cap = ratio * 100
            capped_score = min(evaluation.score, cap)

            print(f"Test results: {execution_result.output}")

            calibrated_score = self._calibration.calibrate(capped_score)

            return evaluation.model_copy(
                update={
                    **execution_metadata,
                    "score": calibrated_score,
                    "feedback": (
                        evaluation.feedback
                        + "\n\n🧪 Test Results\n"
                        + execution_result.output
                    ),
                }
            )

        # ---------------------------------------------------------
        # Successful execution
        # ---------------------------------------------------------

        if execution_result.status == ExecutionStatus.SUCCESS:

            print(
                f"Execution policy applied: SUCCESS "
                f"{execution_result.passed_tests}/{execution_result.total_tests}"
            )

            calibrated_score = self._calibration.calibrate(evaluation.score)

            return evaluation.model_copy(
                update={
                    **execution_metadata,
                    "score": calibrated_score,
                    "feedback": (
                        evaluation.feedback
                        + "\n\n🧪 Test Results\n"
                        + execution_result.output
                    ),
                }
            )

        return evaluation
