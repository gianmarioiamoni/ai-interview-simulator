# feedback_builder.py

from typing import List
from app.ui.presenters.feedback.feedback_models import FeedbackBundle, FeedbackBlockResult


class FeedbackBuilder:

    def build(self, state, result, evaluation, execution) -> FeedbackBundle:

        analysis = self._analyze(execution)

        blocks = self._collect_blocks(
            state, result, evaluation, execution, analysis
        )

        overall_severity = self._aggregate_severity(blocks)
        overall_confidence = self._aggregate_confidence(blocks)

        markdown = self._render_markdown(blocks)

        return FeedbackBundle(
            blocks=blocks,
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            markdown=markdown,
        )

    # -----------------------------------------------------

    def _collect_blocks(self, state, result, evaluation, execution, analysis) -> List[FeedbackBlockResult]:

        collected = []

        for block in self._blocks:
            if block.can_handle(...):
                collected.append(block.build(...))

        return collected

    def _aggregate_severity(self, blocks):

        if any(b.severity == "error" for b in blocks):
            return "error"
        if any(b.severity == "warning" for b in blocks):
            return "warning"
        return "info"


    def _aggregate_confidence(self, blocks):

        if not blocks:
            return 0.0

        return round(sum(b.confidence for b in blocks) / len(blocks), 2)

    def _render_markdown(self, blocks):

        lines = []

        for b in blocks:
            lines.append(f"## {b.title}")
            lines.append(b.content)
            lines.append("")

        return "\n".join(lines)