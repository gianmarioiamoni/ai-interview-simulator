# app/ui/adapters/execution_analysis_adapter.py

from dataclasses import dataclass


@dataclass
class ExecutionAnalysisDTO:
    has_runtime_error: bool
    primary_error: str | None
