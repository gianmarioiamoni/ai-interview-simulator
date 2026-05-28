# services/question_corpus/retrieval/chroma_retrieval_service.py

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from services.question_corpus.constants.vector_store_constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
)
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.retrieval.chroma_filter_builder import ChromaFilterBuilder


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

        self._filter_builder = ChromaFilterBuilder()

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

    def search_with_filters(
        self,
        query: str,
        filters: RetrievalFilters,
        k: int = 5,
    ) -> list[Document]:

        where = self._filter_builder.build(
            filters,
        )

        return self._vectorstore.similarity_search(
            query=query,
            k=k,
            filter=where,
        )
