# services/interview_evaluation/builders/dimension_builder.py

from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS
from domain.contracts.shared.performance_dimension import PerformanceDimension


class DimensionBuilder:

    def build(self, dimension_scores, narrative):

        performance_dimensions = []

        justification_map = narrative.get("dimension_justifications", {})

        for dim, score in dimension_scores.items():

            label = DIMENSION_LABELS.get(dim, dim.value)

            justification = justification_map.get(
                label,
                "Justification unavailable.",
            )

            performance_dimensions.append(
                PerformanceDimension(
                    name=label,
                    score=score,
                    justification=justification,
                )
            )

        return performance_dimensions
