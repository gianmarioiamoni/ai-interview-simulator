## app/ui/adapters/execution_analysis_adapter.py

from typing import Optional

from services.execution_analysis.execution_analyzer import ExecutionAnalysis
from domain.contracts.feedback.feedback.error_type import ErrorType


class ExecutionAnalysisDTO:
    # UI-facing DTO for execution analysis.
    # Keeps separation between domain model and UI layer.

    def __init__(
        self,
        has_global_runtime_error: bool,
        has_test_runtime_errors: bool,
        has_logic_failures: bool,
        primary_error: Optional[str],
        error_type: ErrorType,
    ):
        # -----------------------------------------------------
        # Core flags
        # -----------------------------------------------------

        self.has_global_runtime_error = has_global_runtime_error
        self.has_test_runtime_errors = has_test_runtime_errors
        self.has_logic_failures = has_logic_failures

        # -----------------------------------------------------
        # Error info
        # -----------------------------------------------------

        self.primary_error = primary_error
        self.error_type = error_type  # 🔥 FIX CRITICO

    # ---------------------------------------------------------
    # BACKWARD COMPATIBILITY (important)
    # ---------------------------------------------------------

    @property
    def has_runtime_error(self) -> bool:
        # Legacy compatibility flag.
        
        return self.has_global_runtime_error or self.has_test_runtime_errors


class ExecutionAnalysisAdapter:
    # Adapter: Domain → UI DTO

    @staticmethod
    def to_dto(analysis: Optional[ExecutionAnalysis]) -> Optional[ExecutionAnalysisDTO]:

        if not analysis:
            return None

        return ExecutionAnalysisDTO(
            has_global_runtime_error=analysis.has_global_runtime_error,
            has_test_runtime_errors=analysis.has_test_runtime_errors,
            has_logic_failures=analysis.has_logic_failures,
            primary_error=analysis.primary_error,
            error_type=analysis.error_type,
        )
