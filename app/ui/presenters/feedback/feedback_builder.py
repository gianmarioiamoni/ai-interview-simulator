# app/ui/presenters/feedback/feedback_builder.py

from typing import List

from domain.contracts.interview_state import InterviewState
from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult

from services.execution_analysis.execution_analyzer import ExecutionAnalyzer
from app.ui.adapters.execution_analysis_adapter import ExecutionAnalysisAdapter

from app.ui.presenters.feedback.feedback_models import FeedbackBundle
from app.ui.presenters.feedback.blocks.runtime_error_block import RuntimeErrorBlock
from app.ui.presenters.feedback.blocks.success_block import SuccessBlock
from app.ui.presenters.feedback.blocks.failure_block import FailureBlock
from app.ui.presenters.feedback.blocks.written_block import WrittenBlock
from app.ui.presenters.feedback.blocks.fallback_block import FallbackBlock


class FeedbackBuilder:

    def __init__(self) -> None:
        self._analyzer = ExecutionAnalyzer()

        # Order matters!
        self._blocks = [
            WrittenBlock(),
            RuntimeErrorBlock(),
            SuccessBlock(),
            FailureBlock(),
            FallbackBlock(),
        ]

    # =========================================================
    # PUBLIC API
    # =========================================================

    def build(
        self,
        state: InterviewState,
        result: QuestionResult,
        evaluation: QuestionEvaluation | None,
        execution: ExecutionResult | None,
    ) -> FeedbackBundle:

        # -----------------------------------------------------
        # Analysis (FIX HERE)
        # -----------------------------------------------------

        analysis_raw = self._analyzer.analyze(execution) if execution else None
        analysis = (
            ExecutionAnalysisAdapter.to_dto(analysis_raw)
            if analysis_raw
            else None
        )

        # -----------------------------------------------------
        # Collect blocks
        # -----------------------------------------------------

        blocks = self._collect_blocks(
            state,
            result,
            evaluation,
            execution,
            analysis,
        )

        # -----------------------------------------------------
        # Aggregate
        # -----------------------------------------------------

        overall_severity = self._aggregate_severity(blocks)
        overall_confidence = self._aggregate_confidence(blocks)

        # -----------------------------------------------------
        # Render
        # -----------------------------------------------------

        markdown = self._render_markdown(blocks)

        return FeedbackBundle(
            blocks=blocks,
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            markdown=markdown,
        )

    # =========================================================
    # INTERNALS
    # =========================================================

    def _collect_blocks(
        self,
        state,
        result,
        evaluation,
        execution,
        analysis,
    ):

        for block in self._blocks:
            if block.can_handle(result, evaluation, execution, analysis):
                return [block.build(state, result, evaluation, execution, analysis)]

        return []

    def _aggregate_severity(self, blocks):

        if any(b.severity == "error" for b in blocks):
            return "error"

        if any(b.severity == "warning" for b in blocks):
            return "warning"

        return "info"

    def _aggregate_confidence(self, blocks):

        if not blocks:
            return 0.0

        return sum(b.confidence for b in blocks) / len(blocks)

    def _render_markdown(self, blocks):

        lines: List[str] = []

        for b in blocks:
            lines.append(f"## {b.title}")
            lines.append(b.content)
            lines.append("")

        return "\n".join(lines)
