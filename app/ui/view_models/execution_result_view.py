# app/ui/view_models/execution_result_view.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResultView:
    status: str
    success: bool
    output: str
    error: Optional[str]
    passed_tests: int
    total_tests: int
    execution_time_ms: int
