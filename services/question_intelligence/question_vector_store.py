# services/question_intelligence/question_vector_store.py

# QuestionVectorStore
#
# Responsibility:
# Encapsulates vector store operations for QuestionBankItem.
# It isolates metadata schema, document conversion,
# and collection naming from the rest of the system.

from typing import List

from langchain_core.documents import Document

from domain.contracts.question_bank_item import QuestionBankItem


class QuestionVectorStore:
    def __init__(self, vector_store):
        # vector_store is injected (created via vector_store_factory)
        self._vector_store = vector_store

    def add_items(self, items: List[QuestionBankItem]) -> None:
        documents = [self._to_document(item) for item in items]
        self._vector_store.add_documents(documents)

    def similarity_search(
        self,
        query: str,
        k: int,
        metadata_filter: dict | None = None,
    ) -> List[Document]:
        return self._vector_store.similarity_search(
            query=query,
            k=k,
            filter=metadata_filter,
        )

    def _to_document(self, item: QuestionBankItem) -> Document:
        return Document(
            page_content=item.text,
            metadata={
                "id": item.id,
                "interview_type": item.interview_type,
                "role": item.role,
                "area": item.area,
                "level": item.level,
                "difficulty": item.difficulty,
            },
        )
