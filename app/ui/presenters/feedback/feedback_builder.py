# app/ui/presenters/feedback/feedback_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.quality import Quality

from app.contracts.feedback_bundle import FeedbackBundle

from app.ui.presenters.feedback.pipeline.feedback_block_pipeline import (
    FeedbackBlockPipeline,
)
from app.ui.presenters.feedback.services.execution_analysis_service import (
    ExecutionAnalysisService,
)
from app.ui.presenters.feedback.aggregators.feedback_aggregator import (
    FeedbackAggregator,
)
from app.ui.presenters.feedback.renderers.feedback_markdown_renderer import (
    FeedbackMarkdownRenderer,
)


class FeedbackBuilder:

    def __init__(self) -> None:
        self._analysis_service = ExecutionAnalysisService()
        self._pipeline = FeedbackBlockPipeline()
        self._aggregator = FeedbackAggregator()
        self._renderer = FeedbackMarkdownRenderer()

    def build(
        self,
        state: InterviewState,
        result: QuestionResult,
        evaluation: QuestionEvaluation | None,
        execution: ExecutionResult | None,
        quality: Quality,
    ) -> FeedbackBundle:

        analysis = self._analysis_service.analyze(execution)

        blocks = self._pipeline.build_blocks(
            state,
            result,
            evaluation,
            execution,
            analysis,
            quality,
        )

        overall_severity = self._aggregator.aggregate_severity(blocks)
        overall_confidence = self._aggregator.aggregate_confidence(blocks)

        markdown = self._renderer.render(blocks)

        return FeedbackBundle(
            blocks=blocks,
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            overall_quality=quality,
            markdown=markdown,
        )
