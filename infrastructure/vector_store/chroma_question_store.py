# infrastructure/vector_store/chroma_question_store.py

# ChromaQuestionStore
#
# Responsibility:
# Creates and manages the Chroma collection dedicated
# to QuestionBankItem embeddings.
# Ensures persistence and embedding consistency.

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from infrastructure.embeddings.embedding_factory import get_embedding_model


class ChromaQuestionStore:
    COLLECTION_NAME = "question_bank"
    PERSIST_DIR = Path("data/vector_store")

    def __init__(self) -> None:
        self.PERSIST_DIR.mkdir(parents=True, exist_ok=True)

        self._embedding_model = get_embedding_model()

        self._store = Chroma(
            collection_name=self.COLLECTION_NAME,
            embedding_function=self._embedding_model,
            persist_directory=str(self.PERSIST_DIR),
        )

    def add_documents(self, documents: list[Document]) -> None:
        self._store.add_documents(documents)

    def similarity_search(
        self,
        query: str,
        k: int,
        filter: dict | None = None,
    ):
        return self._store.similarity_search(
            query=query,
            k=k,
            filter=filter,
        )
