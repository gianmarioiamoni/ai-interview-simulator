# services/interview_evaluation/mappers/readable_dimension_mapper.py

from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS


class ReadableDimensionMapper:

    def map(self, dimension_scores):

        readable = [
            {
                "name": DIMENSION_LABELS.get(dim, dim.value),
                "score": score,
            }
            for dim, score in dimension_scores.items()
            if score is not None
        ]


        return readable, None, None
