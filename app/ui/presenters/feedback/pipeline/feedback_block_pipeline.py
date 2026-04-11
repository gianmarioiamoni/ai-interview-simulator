# app/ui/presenters/feedback/pipeline/feedback_block_pipeline.py

from app.ui.presenters.feedback.blocks.runtime_error_block import RuntimeErrorBlock
from app.ui.presenters.feedback.blocks.success_block import SuccessBlock
from app.ui.presenters.feedback.blocks.failure_block import FailureBlock
from app.ui.presenters.feedback.blocks.written_block import WrittenBlock
from app.ui.presenters.feedback.blocks.fallback_block import FallbackBlock
from app.ui.presenters.feedback.blocks.score_block import ScoreBlock
from app.ui.presenters.feedback.blocks.summary_block import SummaryBlock
from app.ui.presenters.feedback.blocks.hint_block import HintBlock
from app.ui.presenters.feedback.blocks.test_breakdown_block import TestBreakdownBlock


class FeedbackBlockPipeline:

    def __init__(self) -> None:
        self._blocks = [
            WrittenBlock(),
            SummaryBlock(),
            ScoreBlock(),
            RuntimeErrorBlock(),
            TestBreakdownBlock(),
            SuccessBlock(),
            FailureBlock(),
            HintBlock(),
            FallbackBlock(),
        ]

    def build_blocks(
        self,
        state,
        result,
        evaluation,
        execution,
        analysis,
        quality,
    ):
        blocks = []

        # -----------------------------------------------------
        # CORE BLOCKS → ALWAYS
        # -----------------------------------------------------

        blocks.extend(
            self._build_core_blocks(
                state, result, evaluation, execution, analysis, quality
            )
        )

        # -----------------------------------------------------
        # OTHER BLOCKS
        # -----------------------------------------------------

        for block in self._blocks:
            if self._is_core(block):
                continue

            if block.can_handle(result, evaluation, execution, analysis):
                built = block.build(
                    state, result, evaluation, execution, analysis, quality
                )
                if built:
                    blocks.append(built)

        return self._order(blocks)

    # =========================================================

    def _build_core_blocks(self, *args):
        state, result, evaluation, execution, analysis, quality = args

        core_blocks = []

        for block in self._blocks:
            if self._is_core(block):
                built = block.build(
                    state, result, evaluation, execution, analysis, quality
                )
                if built:
                    core_blocks.append(built)

        return core_blocks

    # =========================================================

    def _is_core(self, block):
        return block.__class__.__name__ in ("SummaryBlock", "ScoreBlock")

    # =========================================================

    def _order(self, blocks):

        def priority(block):

            if block.title == "Summary":
                return (0, 0)

            if block.title == "Score":
                return (1, 0)

            severity_rank = {
                "error": 0,
                "warning": 1,
                "info": 2,
            }.get(block.severity, 3)

            quality_rank = 0
            if getattr(block, "quality", None):
                try:
                    quality_rank = -block.quality.rank()
                except Exception:
                    pass

            return (2, severity_rank, quality_rank)

        return sorted(blocks, key=priority)
