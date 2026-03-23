# app/ui/presenters/feedback/feedback_builder.py

from typing import Optional

from domain.contracts.interview_state import InterviewState
from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult

from services.execution_analysis.execution_analyzer import ExecutionAnalyzer
from app.ui.adapters.execution_analysis_adapter import ExecutionAnalysisAdapter

from app.ui.presenters.feedback.blocks.runtime_error_block import RuntimeErrorBlock
from app.ui.presenters.feedback.blocks.success_block import SuccessBlock
from app.ui.presenters.feedback.blocks.failure_block import FailureBlock
from app.ui.presenters.feedback.blocks.written_block import WrittenBlock
from app.ui.presenters.feedback.blocks.fallback_block import FallbackBlock


class FeedbackBuilder:

    def __init__(self) -> None:
        self._analyzer = ExecutionAnalyzer()

    def build(
        self,
        state: InterviewState,
        result: QuestionResult,
        evaluation: Optional[QuestionEvaluation],
        execution: Optional[ExecutionResult],
    ) -> str:

        analysis_raw = self._analyzer.analyze(execution) if execution else None
        analysis = ExecutionAnalysisAdapter.to_dto(analysis_raw)

        blocks = [
            WrittenBlock(),
            RuntimeErrorBlock(),
            SuccessBlock(),
            FailureBlock(),
            FallbackBlock(),
        ]

        for block in blocks:
            if block.can_handle(result, evaluation, execution, analysis):
                return block.build(state, result, evaluation, execution, analysis)

        return ""
