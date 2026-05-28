# services/question_corpus/validators/corpus_duplicate_detector.py

from itertools import combinations

from services.question_corpus.contracts.curated_corpus import CuratedCorpus
from services.question_corpus.validations.contracts.corpus_validation_issue import CorpusValidationIssue


class CorpusDuplicateDetector:

    SIMILARITY_THRESHOLD = 0.90

    # =====================================================
    # PUBLIC
    # =====================================================

    def detect(
        self,
        corpus: CuratedCorpus,
    ) -> list[CorpusValidationIssue]:

        issues: list[CorpusValidationIssue] = []

        for q1, q2 in combinations(corpus.questions, 2):

            similarity = self._similarity(
                q1.question,
                q2.question,
            )

            if similarity < self.SIMILARITY_THRESHOLD:
                continue

            issues.append(
                CorpusValidationIssue(
                    severity="warning",
                    category="duplicate",
                    message=(f"Potential duplicate with {q2.id}"),
                    question_id=q1.id,
                )
            )

        return issues

    # =====================================================
    # INTERNALS
    # =====================================================

    def _similarity(
        self,
        a: str,
        b: str,
    ) -> float:

        tokens_a = set(a.lower().split())
        tokens_b = set(b.lower().split())

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a.intersection(tokens_b)

        union = tokens_a.union(tokens_b)

        return len(intersection) / len(union)
