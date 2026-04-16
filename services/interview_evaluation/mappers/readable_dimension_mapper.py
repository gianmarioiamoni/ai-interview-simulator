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

        if readable:
            strongest = max(readable, key=lambda x: x["score"])["name"]
            weakest = min(readable, key=lambda x: x["score"])["name"]
        else:
            strongest = "N/A"
            weakest = "N/A"

        return readable, strongest, weakest
