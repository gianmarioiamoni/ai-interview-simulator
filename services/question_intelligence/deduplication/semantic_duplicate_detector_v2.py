# services/question_intelligence/deduplication/semantic_duplicate_detector_v2.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.semantic.embedding_similarity_engine import (
    EmbeddingSimilarityEngine,
)

from services.question_intelligence.deduplication.semantic_duplicate_report import (
    DuplicatePair,
    SemanticDuplicateReport,
)


class SemanticDuplicateDetectorV2:

    DEFAULT_THRESHOLD = 0.82

    def __init__(self) -> None:

        self._similarity_engine = EmbeddingSimilarityEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def detect(
        self,
        items: List[QuestionBankItem],
        threshold: float = DEFAULT_THRESHOLD,
    ) -> SemanticDuplicateReport:

        duplicates: List[DuplicatePair] = []

        max_similarity = 0.0

        for i in range(len(items)):

            for j in range(i + 1, len(items)):

                similarity = self._similarity_engine.similarity(
                    items[i].text,
                    items[j].text,
                )

                max_similarity = max(
                    max_similarity,
                    similarity,
                )

                if similarity >= threshold:

                    duplicates.append(
                        DuplicatePair(
                            left=items[i].text,
                            right=items[j].text,
                            similarity=similarity,
                        )
                    )

        total_pairs = max(
            (len(items) * (len(items) - 1)) / 2,
            1,
        )

        duplicate_ratio = len(duplicates) / total_pairs

        return SemanticDuplicateReport(
            total_documents=len(items),
            duplicate_pairs=duplicates,
            duplicate_ratio=round(duplicate_ratio, 2),
            max_similarity=round(max_similarity, 2),
        )
