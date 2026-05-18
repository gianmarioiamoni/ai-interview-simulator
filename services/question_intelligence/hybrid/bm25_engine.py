# services/question_intelligence/hybrid/bm25_engine.py

from typing import List

from rank_bm25 import BM25Okapi

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.hybrid.keyword_search_result import (
    KeywordSearchResult,
)


class BM25Engine:

    def __init__(
        self,
        items: List[QuestionBankItem],
    ) -> None:

        self._items = items

        corpus = [item.text.lower().split() for item in items]

        self._bm25 = BM25Okapi(corpus)

    # =====================================================
    # PUBLIC
    # =====================================================

    def search(
        self,
        query: str,
        top_k: int,
    ) -> List[KeywordSearchResult]:

        tokens = query.lower().split()

        scores = self._bm25.get_scores(tokens)

        scored = list(zip(self._items, scores))

        scored.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        results = []

        for item, score in scored[:top_k]:

            results.append(
                KeywordSearchResult(
                    text=item.text,
                    score=round(
                        float(score),
                        2,
                    ),
                )
            )

        return results
