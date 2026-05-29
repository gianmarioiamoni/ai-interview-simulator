# services/question_corpus/retrieval/hybrid_retrieval_scorer.py

from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.contracts.retrieval_result import RetrievalResult


class HybridRetrievalScorer:

    # =====================================================
    # CONSTANTS
    # =====================================================

    SEMANTIC_WEIGHT = 0.75

    QUALITY_WEIGHT = 0.25

    # =====================================================
    # PUBLIC
    # =====================================================

    def score(
        self,
        result: RetrievalResult,
    ) -> RetrievalCandidate:

        final_score = (
            result.semantic_score * self.SEMANTIC_WEIGHT
            + result.quality_score * self.QUALITY_WEIGHT
        )

        return RetrievalCandidate(
            document=result.document,
            semantic_score=round(
                result.semantic_score,
                3,
            ),
            quality_score=round(
                result.quality_score,
                3,
            ),
            final_score=round(
                final_score,
                3,
            ),
            diversity_score=round(
                final_score,
                3,
            ),
            adaptive_score=round(
                final_score,
                3,
            ),
            embedding=result.embedding,
        )
