# services/question_corpus/retrieval/chroma_retrieval_service.py
#
# Internal implementation detail. External callers must use
# QuestionRetrievalRuntime instead of importing this module directly.

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from services.question_corpus.constants.vector_store_constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
)
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.chroma_filter_builder import ChromaFilterBuilder
from services.question_corpus.retrieval.hybrid_retrieval_scorer import HybridRetrievalScorer
from services.question_corpus.retrieval.diversity_reranker import DiversityReranker


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

        results = self._vectorstore.similarity_search_with_score(
            query=query,
            k=k,
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

        results = self._vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=where,
        )

        
        return self._score_results(
            results,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _score_results(
        self,
        results: list[tuple[Document, float]],
    ) -> list[RetrievalCandidate]:

        candidates: list[RetrievalCandidate] = []

        for document, distance in results:

            candidate = self._scorer.score(
                document=document,
                semantic_distance=distance,
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
