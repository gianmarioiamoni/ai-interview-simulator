## app/ui/presenters/feedback/services/execution_analysis_service.py

from domain.contracts.error_type import ErrorType
from domain.contracts.execution_result import ExecutionResult, ExecutionStatus

from services.execution_analysis.execution_analyzer import ExecutionAnalysis


class ExecutionAnalysisService:

    def analyze(self, execution: ExecutionResult | None) -> ExecutionAnalysis | None:

        if not execution:
            return None

        # -----------------------------------------------------
        # NO ERROR CASE
        # -----------------------------------------------------

        if execution.success:
            return ExecutionAnalysis(
                has_runtime_error=False,
                primary_error=None,
                error_type=ErrorType.UNKNOWN,
            )

        error = execution.error or ""

        # -----------------------------------------------------
        # CLASSIFICATION
        # -----------------------------------------------------

        error_type = self._classify_error(execution, error)

        return ExecutionAnalysis(
            has_runtime_error=True,
            primary_error=error,
            error_type=error_type,
            is_signature_error=(error_type == ErrorType.SIGNATURE),
        )

    # =========================================================

    def _classify_error(
        self,
        execution: ExecutionResult,
        error: str,
    ) -> ErrorType:

        # -----------------------------------------------------
        # STATUS-BASED
        # -----------------------------------------------------

        if execution.status == ExecutionStatus.SYNTAX_ERROR:
            return ErrorType.SYNTAX

        if execution.status == ExecutionStatus.TIMEOUT:
            return ErrorType.TIMEOUT

        # -----------------------------------------------------
        # SIGNATURE DETECTION
        # -----------------------------------------------------

        if "__SIGNATURE_WARNING__" in execution.output:
            return ErrorType.SIGNATURE

        if "Invalid signature" in error:
            return ErrorType.SIGNATURE

        # -----------------------------------------------------
        # COMMON RUNTIME PATTERNS
        # -----------------------------------------------------

        if "NameError" in error:
            return ErrorType.RUNTIME

        if "TypeError" in error:
            return ErrorType.RUNTIME

        if "AttributeError" in error:
            return ErrorType.RUNTIME

        # -----------------------------------------------------
        # FALLBACK
        # -----------------------------------------------------

        return ErrorType.RUNTIME
