# app/ui/presenters/feedback/aggregators/feedback_aggregator.py

from services.feedback_aggregation import (
    compute_overall_confidence,
    compute_overall_severity,
)


class FeedbackAggregator:

    def aggregate_severity(self, blocks):
        return compute_overall_severity(blocks)

    def aggregate_confidence(self, blocks):
        return compute_overall_confidence(blocks)
