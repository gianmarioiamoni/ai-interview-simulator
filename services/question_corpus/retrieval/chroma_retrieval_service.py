# services/question_corpus/retrieval/chroma_retrieval_service.py

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from services.question_corpus.constants.vector_store_constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
)


class ChromaRetrievalService:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=OpenAIEmbeddings(),
            persist_directory=CHROMA_PERSIST_DIRECTORY,
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> list[Document]:

        return self._vectorstore.similarity_search(
            query=query,
            k=k,
        )
