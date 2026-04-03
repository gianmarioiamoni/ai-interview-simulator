# app/ui/presenters/feedback/feedback_builder.py

from typing import List

from domain.contracts.interview_state import InterviewState
from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult

from services.execution_analysis.execution_analyzer import ExecutionAnalyzer
from app.ui.adapters.execution_analysis_adapter import ExecutionAnalysisAdapter

from app.contracts.feedback_bundle import FeedbackBundle

from app.ui.presenters.feedback.blocks.runtime_error_block import RuntimeErrorBlock
from app.ui.presenters.feedback.blocks.success_block import SuccessBlock
from app.ui.presenters.feedback.blocks.failure_block import FailureBlock
from app.ui.presenters.feedback.blocks.written_block import WrittenBlock
from app.ui.presenters.feedback.blocks.fallback_block import FallbackBlock
from app.ui.presenters.feedback.blocks.score_block import ScoreBlock
from app.ui.presenters.feedback.blocks.summary_block import SummaryBlock


class FeedbackBuilder:

    def __init__(self) -> None:
        self._analyzer = ExecutionAnalyzer()

        self._blocks = [
            WrittenBlock(),
            SummaryBlock(),
            ScoreBlock(),
            RuntimeErrorBlock(),
            SuccessBlock(),
            FailureBlock(),
            FallbackBlock(),
        ]

    # =========================================================

    def build(
        self,
        state: InterviewState,
        result: QuestionResult,
        evaluation: QuestionEvaluation | None,
        execution: ExecutionResult | None,
    ) -> FeedbackBundle:

        analysis_raw = self._analyzer.analyze(execution) if execution else None
        analysis = (
            ExecutionAnalysisAdapter.to_dto(analysis_raw) if analysis_raw else None
        )

        blocks = self._collect_blocks(
            state,
            result,
            evaluation,
            execution,
            analysis,
        )

        overall_severity = self._aggregate_severity(blocks)
        overall_confidence = self._aggregate_confidence(blocks)

        # 🔥 QUALITY: SINGLE SOURCE OF TRUTH (STATE)
        state_bundle = getattr(state, "last_feedback_bundle", None)
        overall_quality = (
            state_bundle.overall_quality
            if state_bundle and state_bundle.overall_quality
            else "incorrect"
        )

        markdown = self._render_markdown(blocks)

        return FeedbackBundle(
            blocks=blocks,
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            overall_quality=overall_quality,
            markdown=markdown,
        )

    # =========================================================

    def _collect_blocks(
        self,
        state,
        result,
        evaluation,
        execution,
        analysis,
    ):

        blocks = []

        # CORE BLOCKS
        if execution:
            for block in self._blocks:
                if isinstance(block, (SummaryBlock, ScoreBlock)):
                    built = block.build(
                        state,
                        result,
                        evaluation,
                        execution,
                        analysis,
                    )
                    if built:
                        blocks.append(built)

        # OTHER BLOCKS
        for block in self._blocks:

            if isinstance(block, (SummaryBlock, ScoreBlock)):
                continue

            if block.can_handle(result, evaluation, execution, analysis):

                built = block.build(
                    state,
                    result,
                    evaluation,
                    execution,
                    analysis,
                )

                if built:
                    blocks.append(built)

        return blocks

    # =========================================================

    def _aggregate_severity(self, blocks):

        if any(b.severity == "error" for b in blocks):
            return "error"

        if any(b.severity == "warning" for b in blocks):
            return "warning"

        return "info"

    def _aggregate_confidence(self, blocks):

        if not blocks:
            return 0.0

        weights = {
            "error": 1.0,
            "warning": 0.7,
            "info": 0.5,
        }

        total = 0.0
        weight_sum = 0.0

        for b in blocks:
            w = weights.get(b.severity, 0.5)
            total += b.confidence * w
            weight_sum += w

        return round(total / weight_sum if weight_sum else 0.0, 2)

    def _render_markdown(self, blocks):

        lines: List[str] = []

        for b in blocks:
            lines.append(f"## {b.title}")
            lines.append(b.content)
            lines.append("")

        return "\n".join(lines)
