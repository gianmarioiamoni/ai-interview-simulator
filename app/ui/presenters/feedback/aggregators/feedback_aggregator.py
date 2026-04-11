# app/ui/presenters/feedback/aggregators/feedback_aggregator.py

from domain.contracts.severity import Severity


class FeedbackAggregator:

    def aggregate_severity(self, blocks):

        if not blocks:
            return Severity.INFO

        # 🔥 usa rank invece di if multipli
        return min((b.severity for b in blocks), key=lambda s: s.rank())

    def aggregate_confidence(self, blocks):

        if not blocks:
            return 0.0

        total = sum(
            b.severity.weighted_confidence(b.confidence) 
            for b in blocks
        )

        weight_sum = sum(b.severity.weight() for b in blocks)

        return round(total / weight_sum if weight_sum else 0.0, 2)
