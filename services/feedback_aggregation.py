# services/feedback_aggregation.py

from domain.contracts.feedback.severity import Severity


def compute_overall_confidence(blocks) -> float:
    # Compute weighted confidence across feedback blocks.
    # Domain-level logic:
    # - severity drives weight
    # - confidence is weighted accordingly
    if not blocks:
        return 0.0

    total = sum(b.severity.weighted_confidence(b.confidence) for b in blocks)

    weight_sum = sum(b.severity.weight() for b in blocks)

    return round(total / weight_sum if weight_sum else 0.0, 2)


def compute_overall_severity(blocks) -> Severity:
    # Compute worst severity across blocks.
    # Lower rank = higher severity.
    if not blocks:
        return Severity.INFO
    return min((b.severity for b in blocks), key=lambda s: s.rank())
