# services/question_intelligence/reranking/coverage_constrained_reranker.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.coverage.topic_extractor import (
    TopicExtractor,
)

from services.question_intelligence.reranking.reranked_result import (
    RerankedResult,
)

from services.question_intelligence.reranking.retrieval_reranker import (
    RetrievalReranker,
)


class CoverageConstrainedReranker:

    DEFAULT_MAX_PER_TOPIC = 2

    def __init__(self) -> None:

        self._topic_extractor = TopicExtractor()

        self._base_reranker = RetrievalReranker()

    # =====================================================
    # PUBLIC
    # =====================================================

    def rerank(
        self,
        items: List[QuestionBankItem],
        target_count: int,
        max_per_topic: int,
    ) -> List[RerankedResult]:

        reranked = self._base_reranker.rerank(
            items=items,
            target_count=len(items),
        )

        selected: List[RerankedResult] = []

        topic_counts: dict[str, int] = {}

        for result in reranked:

            topic = self._topic_extractor.extract(
                result.item.text,
            )

            current_count = topic_counts.get(
                topic,
                0,
            )

            if current_count >= max_per_topic:
                continue

            selected.append(result)

            topic_counts[topic] = current_count + 1

            if len(selected) >= target_count:
                break

        return selected
