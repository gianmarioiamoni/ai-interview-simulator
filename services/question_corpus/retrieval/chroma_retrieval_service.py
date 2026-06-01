# services/question_corpus/retrieval/chroma_retrieval_service.py

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from services.question_corpus.constants.vector_store_constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
)
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.contracts.retrieval_result import RetrievalResult
from services.question_corpus.retrieval.chroma_filter_builder import ChromaFilterBuilder
from services.question_corpus.retrieval.hybrid_retrieval_scorer import HybridRetrievalScorer
from services.question_corpus.retrieval.diversity_reranker import DiversityReranker
from services.question_corpus.adapters.chroma_result_adapter import ChromaResultAdapter


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

        print(type(self._vectorstore._embedding_function))

        self._filter_builder = ChromaFilterBuilder()

        self._result_adapter = ChromaResultAdapter()

        self._scorer = HybridRetrievalScorer()

        self._diversity_reranker = DiversityReranker()

    # =====================================================
    # PUBLIC
    # =====================================================

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> list[RetrievalCandidate]:

        raw_results = self._query_chroma(
            query=query,
            k=k,
            where=None,
        )

        results = self._result_adapter.adapt(
            raw_results,
        )

        return self._score_results(
            results,
        )

    def search_with_filters(
        self,
        query: str,
        filters: RetrievalFilters,
        k: int = 5,
    ) -> list[RetrievalCandidate]:

        where = self._filter_builder.build(
            filters,
        )

        raw_results = self._query_chroma(
            query=query,
            k=k,
            where=where,
        )

        results = self._result_adapter.adapt(
            raw_results,
        )

        return self._score_results(
            results,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _query_chroma(
        self,
        query: str,
        k: int,
        where: dict | None,
    ) -> dict:

        collection = self._vectorstore._collection

        print(collection.metadata)

        return collection.query(
            query_texts=[
                query,
            ],
            n_results=k,
            where=where,
            include=[
                "documents",
                "metadatas",
                "distances",
                "embeddings",
            ],
        )

    def _score_results(
        self,
        results: list[RetrievalResult],
    ) -> list[RetrievalCandidate]:

        candidates: list[RetrievalCandidate] = []

        for result in results:

            candidate = self._scorer.score(
                result,
            )

            candidates.append(
                candidate,
            )

        candidates.sort(
            key=lambda c: c.final_score,
            reverse=True,
        )

        reranked = self._diversity_reranker.rerank(
            candidates=candidates,
            top_k=len(candidates),
        )

        return reranked
