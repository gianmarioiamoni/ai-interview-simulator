# services/feedback/dimension_aggregator.py

from collections import Counter
from typing import Dict, List

from domain.contracts.shared.performance_dimension_type import (
    PerformanceDimensionType,
)
from domain.contracts.feedback.feedback import FeedbackBlockResult


class FeedbackDimensionAggregator:

    @staticmethod
    def aggregate(
        blocks: List[FeedbackBlockResult],
    ) -> Dict[PerformanceDimensionType, float]:

        counter = Counter()

        # -----------------------------------------------------
        # COUNT DIMENSIONS
        # -----------------------------------------------------

        for block in blocks:

            if not block.metadata:
                continue

            dim_value = block.metadata.get("dimension")

            if not dim_value:
                continue

            try:
                dim = PerformanceDimensionType(dim_value)
                counter[dim] += 1
            except Exception:
                continue

        if not counter:
            return {}

        total = sum(counter.values())

        # -----------------------------------------------------
        # NORMALIZE → distribution
        # -----------------------------------------------------

        return {dim: round(count / total, 2) for dim, count in counter.items()}
