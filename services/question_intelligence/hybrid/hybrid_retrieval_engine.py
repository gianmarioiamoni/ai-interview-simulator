# services/question_intelligence/hybrid/hybrid_retrieval_engine.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.hybrid.bm25_engine import (
    BM25Engine,
)

from services.question_intelligence.hybrid.hybrid_retrieval_result import (
    HybridRetrievalResult,
)

from services.question_intelligence.semantic.embedding_similarity_engine import (
    EmbeddingSimilarityEngine,
)


class HybridRetrievalEngine:

    def __init__(
        self,
        items: List[QuestionBankItem],
    ) -> None:

        self._items = items

        self._bm25 = BM25Engine(
            items,
        )

        self._similarity_engine = EmbeddingSimilarityEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def search(
        self,
        query: str,
        top_k: int,
    ) -> List[HybridRetrievalResult]:

        keyword_results = self._bm25.search(
            query=query,
            top_k=len(self._items),
        )

        max_keyword_score = max(
            r.score
            for r in keyword_results
        )

        keyword_scores = {
            r.text: (
                r.score / max_keyword_score
            )
            for r in keyword_results
        }

        results = []

        for item in self._items:

            semantic_score = self._similarity_engine.similarity(
                query,
                item.text,
            )

            keyword_score = keyword_scores.get(
                item.text,
                0.0,
            )

            final_score = semantic_score * 0.7 + keyword_score * 0.3

            results.append(
                HybridRetrievalResult(
                    text=item.text,
                    semantic_score=round(
                        semantic_score,
                        2,
                    ),
                    keyword_score=round(
                        keyword_score,
                        2,
                    ),
                    final_score=round(
                        final_score,
                        2,
                    ),
                )
            )

        results.sort(
            key=lambda r: r.final_score,
            reverse=True,
        )

        return results[:top_k]
