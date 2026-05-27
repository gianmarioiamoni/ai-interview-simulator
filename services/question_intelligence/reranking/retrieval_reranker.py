# services/question_intelligence/reranking/retrieval_reranker.py

from typing import List

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.question_intelligence.semantic.embedding_similarity_engine import EmbeddingSimilarityEngine
from services.question_intelligence.reranking.reranked_result import RerankedResult


class RetrievalReranker:

    REDUNDANCY_THRESHOLD = 0.55

    def __init__(self) -> None:

        self._similarity_engine = EmbeddingSimilarityEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def rerank(
        self,
        items: List[QuestionBankItem],
        target_count: int,
    ) -> List[RerankedResult]:

        selected: List[QuestionBankItem] = []

        results: List[RerankedResult] = []

        for item in items:

            redundancy_penalty = self._compute_redundancy_penalty(
                item,
                selected,
            )

            semantic_score = 1.0

            final_score = semantic_score - redundancy_penalty

            results.append(
                RerankedResult(
                    item=item,
                    semantic_score=round(
                        semantic_score,
                        2,
                    ),
                    redundancy_penalty=round(
                        redundancy_penalty,
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

        return results

    # =====================================================
    # INTERNALS
    # =====================================================

    def _compute_redundancy_penalty(
        self,
        candidate: QuestionBankItem,
        selected: List[QuestionBankItem],
    ) -> float:

        if not selected:
            return 0.0

        similarities = []

        for item in selected:

            similarity = self._similarity_engine.similarity(
                candidate.text,
                item.text,
            )

            similarities.append(similarity)

        max_similarity = max(similarities)

        if max_similarity < self.REDUNDANCY_THRESHOLD:
            return 0.0

        return round(max_similarity * 0.5, 2)
