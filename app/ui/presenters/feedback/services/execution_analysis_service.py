# app/ui/presenters/feedback/services/execution_analysis_service.py

from services.execution_analysis.execution_analyzer import ExecutionAnalyzer
from app.ui.adapters.execution_analysis_adapter import ExecutionAnalysisAdapter


class ExecutionAnalysisService:

    def __init__(self):
        self._analyzer = ExecutionAnalyzer()

    def analyze(self, execution):

        if not execution:
            return None

        # -----------------------------------------------------
        # RAW DOMAIN ANALYSIS
        # -----------------------------------------------------

        analysis_raw = self._analyzer.analyze(execution)

        if not analysis_raw:
            return None

        # -----------------------------------------------------
        # ADAPT TO UI DTO
        # -----------------------------------------------------

        return ExecutionAnalysisAdapter.to_dto(analysis_raw)
