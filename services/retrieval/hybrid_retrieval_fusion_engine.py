# services/retrieval/hybrid_retrieval_fusion_engine.py

from services.retrieval.contracts import (
    RetrievalResult,
    EmbeddingRecord,
    HybridRetrievalResult,
)

from services.retrieval.embedding_similarity_engine import (
    EmbeddingSimilarityEngine,
)


class HybridRetrievalFusionEngine:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self) -> None:

        self._embedding_engine = EmbeddingSimilarityEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def fuse(
        self,
        query: str,
        symbolic_results: list[RetrievalResult],
        embedding_records: list[EmbeddingRecord],
    ) -> list[HybridRetrievalResult]:

        # -------------------------------------------------
        # EMBEDDING RANKING
        # -------------------------------------------------

        embedding_rankings = self._embedding_engine.rank(
            query=query,
            records=(embedding_records),
        )

        similarity_map = {
            record.content: similarity
            for (
                record,
                similarity,
            ) in embedding_rankings
        }

        # -------------------------------------------------
        # FUSION
        # -------------------------------------------------

        fused: list[HybridRetrievalResult] = []

        for result in symbolic_results:

            content = result.record.content

            similarity = similarity_map.get(
                content,
                0.0,
            )

            fused_score = self._calculate_fused_score(
                symbolic_score=(result.final_score),
                embedding_similarity=(similarity),
                semantic_overlap=(result.semantic_overlap),
            )

            fused.append(
                HybridRetrievalResult(
                    symbolic_result=(result),
                    embedding_similarity=(
                        round(
                            similarity,
                            4,
                        )
                    ),
                    fused_score=(
                        round(
                            fused_score,
                            4,
                        )
                    ),
                )
            )

        # -------------------------------------------------
        # SORTING
        # -------------------------------------------------

        fused.sort(
            key=lambda item: (item.fused_score),
            reverse=True,
        )

        return fused

    # =====================================================
    # INTERNALS
    # =====================================================

    def _calculate_fused_score(
        self,
        symbolic_score: float,
        embedding_similarity: float,
        semantic_overlap: float,
    ) -> float:

        # ---------------------------------------------
        # GOVERNANCE-FIRST FUSION
        # ---------------------------------------------

        symbolic_component = symbolic_score * 0.7

        embedding_component = embedding_similarity * 0.2

        overlap_component = semantic_overlap * 0.1

        return symbolic_component + embedding_component + overlap_component
