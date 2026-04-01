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

        # Order matters!
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
        # Analysis
        # -----------------------------------------------------

        analysis_raw = self._analyzer.analyze(execution) if execution else None
        analysis = (
            ExecutionAnalysisAdapter.to_dto(analysis_raw) if analysis_raw else None
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
        overall_quality = self._aggregate_quality(blocks)

        # -----------------------------------------------------
        # Render
        # -----------------------------------------------------

        markdown = self._render_markdown(blocks)

        return FeedbackBundle(
            blocks=blocks,
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            overall_quality=overall_quality,
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

        blocks = []

        # -----------------------------------------------------
        # FORCE CORE BLOCKS (🔥 Summary + Score)
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # NORMAL BLOCKS
        # -----------------------------------------------------

        for block in self._blocks:

            # Skip already added core blocks
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

    def _aggregate_quality(self, blocks):

        if not blocks:
            return None

        # ASC priority order
        priority = ["incorrect", "partial", "inefficient", "correct", "optimal"]

        levels = [b.quality.level for b in blocks if b.quality]

        if not levels:
            return None

        # take the worst
        for level in priority:
            if level in levels:
                return level

        return "correct"

    def _render_markdown(self, blocks):

        lines: List[str] = []

        for b in blocks:
            lines.append(f"## {b.title}")
            lines.append(b.content)
            lines.append("")

            if b.quality:
                lines.append(f"**Quality:** {b.quality.level}")
                lines.append(f"{b.quality.explanation}")
                lines.append("")

        return "\n".join(lines)
