# app/ui/presenters/mappers/execution_mapper.py

from typing import List
from domain.contracts.execution_result import ExecutionResult
from app.ui.view_models.execution_result_view import ExecutionResultView


class ExecutionMapper:

    @staticmethod
    def map(results: List[ExecutionResult]) -> List[ExecutionResultView]:
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
