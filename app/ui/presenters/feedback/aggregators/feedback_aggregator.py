# app/ui/presenters/feedback/aggregators/feedback_aggregator.py


from domain.contracts.severity import Severity

class FeedbackAggregator:

    def aggregate_severity(self, blocks):

        if any(b.severity == Severity.ERROR for b in blocks):
            return Severity.ERROR,

        if any(b.severity == Severity.WARNING for b in blocks):
            return Severity.WARNING,

        return Severity.INFO,

    def aggregate_confidence(self, blocks):

        if not blocks:
            return 0.0

        total = 0.0
        weight_sum = 0.0

        for b in blocks:
            w = b.severity.weight()
            total += b.confidence * w
            weight_sum += w

        return round(total / weight_sum if weight_sum else 0.0, 2)
