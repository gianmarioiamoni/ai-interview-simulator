# services/feedback_bundle_factory.py

from domain.contracts.feedback.feedback import FeedbackBundle

from services.feedback_aggregation import (
    compute_overall_confidence,
    compute_overall_severity,
)


class FeedbackBundleFactory:

    @staticmethod
    def create(
        *,
        blocks,
        quality,
        markdown: str,
    ) -> FeedbackBundle:

        overall_severity = compute_overall_severity(blocks)
        overall_confidence = compute_overall_confidence(blocks)

        return FeedbackBundle(
            blocks=blocks,
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            overall_quality=quality,
            markdown=markdown,
        )
