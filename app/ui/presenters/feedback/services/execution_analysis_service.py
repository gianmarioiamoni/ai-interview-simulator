# app/ui/presenters/feedback/services/execution_analysis_service.py

from domain.contracts.execution_result import ExecutionResult

from services.execution_analysis.execution_analyzer import ExecutionAnalyzer
from app.ui.adapters.execution_analysis_adapter import ExecutionAnalysisAdapter


class ExecutionAnalysisService:

    def __init__(self) -> None:
        self._analyzer = ExecutionAnalyzer()

    def analyze(self, execution: ExecutionResult | None):
        if not execution:
            return None

        raw = self._analyzer.analyze(execution)
        if not raw:
            return None

        return ExecutionAnalysisAdapter.to_dto(raw)
