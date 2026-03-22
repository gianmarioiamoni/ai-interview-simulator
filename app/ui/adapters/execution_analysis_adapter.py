# app/ui/adapters/execution_analysis_adapter.py

from services.execution_analysis.execution_analyzer import ExecutionAnalysis

from app.ui.adapters.execution_analysis_dto import ExecutionAnalysisDTO

class ExecutionAnalysisAdapter:

    @staticmethod
    def to_dto(analysis: ExecutionAnalysis | None) -> ExecutionAnalysisDTO | None:

        if analysis is None:
            return None

        has_runtime_error = getattr(
            analysis, "has_global_runtime_error", False
        ) or getattr(analysis, "has_test_runtime_errors", False)

        primary_error = getattr(analysis, "primary_error", None)

        return ExecutionAnalysisDTO(
            has_runtime_error=has_runtime_error,
            primary_error=primary_error,
        )
