# services/retrieval/retrieval_adaptation_signal_builder.py

from services.retrieval.contracts.retrieval_adaptation_signal import RetrievalAdaptationSignal


class RetrievalAdaptationSignalBuilder:

    LOW_SCORE_THRESHOLD = 60

    def build(
        self,
        results,
    ) -> RetrievalAdaptationSignal:

        weak_areas = []

        repeated_failures = False

        low_scores = 0

        for result in results.values():

            if result.evaluation is None:
                continue

            score = result.evaluation.score

            if score < self.LOW_SCORE_THRESHOLD:

                low_scores += 1

                area = result.question.area

                if area not in weak_areas:
                    weak_areas.append(area)

        if low_scores >= 2:
            repeated_failures = True

        return RetrievalAdaptationSignal(
            weak_areas=weak_areas,
            repeated_failures=repeated_failures,
            low_confidence=(low_scores > 0),
        )
