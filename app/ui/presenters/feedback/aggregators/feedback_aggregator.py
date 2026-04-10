# app/ui/presenters/feedback/aggregators/feedback_aggregator.py


class FeedbackAggregator:

    def aggregate_severity(self, blocks):

        if any(b.severity == "error" for b in blocks):
            return "error"

        if any(b.severity == "warning" for b in blocks):
            return "warning"

        return "info"

    def aggregate_confidence(self, blocks):

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
