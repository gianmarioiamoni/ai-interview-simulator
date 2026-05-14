# services/question_ingestion/indexers/question_vector_indexer.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)


class QuestionVectorIndexer:

    def __init__(
        self,
        vector_store: QuestionVectorStore,
    ) -> None:

        self._vector_store = vector_store

    # =====================================================
    # PUBLIC
    # =====================================================

    def index(
        self,
        items: List[QuestionBankItem],
    ) -> int:

        self._vector_store.add_items(
            items,
        )

        return len(items)
