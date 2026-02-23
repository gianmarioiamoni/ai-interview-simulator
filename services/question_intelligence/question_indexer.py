# services/question_intelligence/question_indexer.py

# QuestionIndexer
#
# Responsibility:
# Synchronizes QuestionBankItems from SQLite
# into the vector store.
# This is a bootstrap operation for the RAG layer.

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)
from infrastructure.persistence.sqlite.question_bank_repository import (
    QuestionBankRepository,
)


class QuestionIndexer:
    def __init__(
        self,
        repository: QuestionBankRepository,
        vector_store: QuestionVectorStore,
    ) -> None:
        self._repository = repository
        self._vector_store = vector_store

    def sync(self) -> int:
        items = self._repository.list_all()

        if not items:
            return 0

        self._vector_store.add_items(items)

        return len(items)
