# services/question_intelligence/diagnostics/retrieval_similarity_engine.py

from typing import List
from difflib import SequenceMatcher

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class RetrievalSimilarityEngine:

    # =====================================================
    # PUBLIC
    # =====================================================

    def compute_pairwise_similarity(
        self,
        items: List[QuestionBankItem],
    ) -> List[float]:

        similarities: List[float] = []

        for i in range(len(items)):

            for j in range(i + 1, len(items)):

                score = self._similarity(
                    items[i].text,
                    items[j].text,
                )

                similarities.append(score)

        return similarities

    # =====================================================
    # INTERNALS
    # =====================================================

    def _similarity(
        self,
        a: str,
        b: str,
    ) -> float:

        return SequenceMatcher(
            None,
            a.lower(),
            b.lower(),
        ).ratio()
