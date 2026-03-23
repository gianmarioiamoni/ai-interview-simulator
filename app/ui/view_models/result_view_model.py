# app/ui/view_models/result_view_model.py

from dataclasses import dataclass
from typing import List

from app.ui.view_models.execution_result_view import ExecutionResultView


@dataclass
class ResultViewModel:
    score: float
    feedback_markdown: str
    execution_results: List[ExecutionResultView]
    errors: List[str]
    passed: bool
