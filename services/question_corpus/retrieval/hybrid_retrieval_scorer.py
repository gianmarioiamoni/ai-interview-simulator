# services/question_corpus/retrieval/hybrid_retrieval_scorer.py

from langchain_core.documents import Document

from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate


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
        document: Document,
        semantic_distance: float,
    ) -> RetrievalCandidate:

        semantic_score = max(
            0.0,
            1.0 - semantic_distance,
        )

        quality_score = float(
            document.metadata.get(
                "quality_score",
                0.5,
            )
        )

        final_score = (
            semantic_score * self.SEMANTIC_WEIGHT + quality_score * self.QUALITY_WEIGHT
        )

        print(
            "EMBEDDING:",
            getattr(
                document,
                "embedding",
                None,
            )
            is not None,
        )

        return RetrievalCandidate(
            document=document,
            semantic_score=round(
                semantic_score,
                3,
            ),
            quality_score=round(
                quality_score,
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
            embedding=getattr(
                document,
                "embedding",
                None,
            ),
        )
