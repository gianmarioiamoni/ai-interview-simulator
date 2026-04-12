# app/ui/presenters/feedback/feedback_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.feedback.feedback.quality import Quality

from services.feedback_bundle_factory import FeedbackBundleFactory

from app.contracts.feedback_bundle import FeedbackBundle

from app.ui.presenters.feedback.pipeline.feedback_block_pipeline import (
    FeedbackBlockPipeline,
)
from app.ui.presenters.feedback.services.execution_analysis_service import (
    ExecutionAnalysisService,
)
from app.ui.presenters.feedback.renderers.feedback_markdown_renderer import (
    FeedbackMarkdownRenderer,
)


class FeedbackBuilder:

    def __init__(self) -> None:
        self._analysis_service = ExecutionAnalysisService()
        self._pipeline = FeedbackBlockPipeline()
        self._renderer = FeedbackMarkdownRenderer()

    def build(
        self,
        state: InterviewState,
        result: QuestionResult,
        evaluation: QuestionEvaluation | None,
        execution: ExecutionResult | None,
        quality: Quality,
    ) -> FeedbackBundle:

        # ANALYSIS ONLY IF NEEDED
        analysis = None
        if execution:
            analysis = self._analysis_service.analyze(execution)

        blocks = self._pipeline.build_blocks(
            state,
            result,
            evaluation,
            execution,
            analysis,
            quality,
        )

        markdown = self._renderer.render(blocks)

        return FeedbackBundleFactory.create(
            blocks=blocks,
            quality=quality,
            markdown=markdown,
        )
