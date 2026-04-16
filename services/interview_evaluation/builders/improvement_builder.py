# services/interview_evaluation/builders/improvement_builder.py

from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS


class ImprovementBuilder:

    def build(self, dimension_scores, narrative):

        missing_dims = [
            DIMENSION_LABELS.get(dim, dim.value)
            for dim, score in dimension_scores.items()
            if score is None
        ]

        improvements = narrative.get("improvement_suggestions", []) or []

        if missing_dims:
            improvements += [
                f"{dim} was not assessed → consider practicing this area."
                for dim in missing_dims
            ]

        return improvements
