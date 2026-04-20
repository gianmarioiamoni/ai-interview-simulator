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
            strongest_entry = max(readable, key=lambda x: x["score"])
            weakest_entry = min(readable, key=lambda x: x["score"])

            strongest = strongest_entry["name"]
            weakest = weakest_entry["name"]

            strongest_score = strongest_entry["score"]
            weakest_score = weakest_entry["score"]

        else:
            strongest = "N/A"
            weakest = "N/A"
            strongest_score = None
            weakest_score = None

        return readable, strongest, weakest, strongest_score, weakest_score
