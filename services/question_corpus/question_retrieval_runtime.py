# services/question_corpus/question_retrieval_runtime.py
#
# QuestionRetrievalRuntime is the sole public entry point for question_corpus
# retrieval operations. External callers must not import AdaptiveRetrievalService
# or ChromaRetrievalService directly.

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.retrieval.adaptive_context_builder import (
    AdaptiveContextBuilder,
)
from services.question_corpus.retrieval.adaptive_retrieval_service import (
    AdaptiveRetrievalService,
)
from services.question_corpus.retrieval.chroma_retrieval_service import (
    ChromaRetrievalService,
)


class QuestionRetrievalRuntime:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        adaptive_retrieval_service: AdaptiveRetrievalService | None = None,
        chroma_retrieval_service: ChromaRetrievalService | None = None,
        context_builder: AdaptiveContextBuilder | None = None,
    ) -> None:

        self._adaptive_retrieval_service = (
            adaptive_retrieval_service
            if adaptive_retrieval_service is not None
            else AdaptiveRetrievalService()
        )

        self._chroma_retrieval_service = (
            chroma_retrieval_service
            if chroma_retrieval_service is not None
            else ChromaRetrievalService()
        )

        self._context_builder = (
            context_builder
            if context_builder is not None
            else AdaptiveContextBuilder()
        )

    # =====================================================
    # PUBLIC — ADAPTIVE RETRIEVAL
    # =====================================================

    def retrieve_questions(
        self,
        query: str,
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalCandidate]:

        return self._adaptive_retrieval_service.retrieve(
            query=query,
            context=context,
        )

    def retrieve_questions_from_memory(
        self,
        query: str,
        memory: InterviewRetrievalMemory,
        role: str,
        seniority: str,
        area: str,
        question_count: int,
    ) -> list[RetrievalCandidate]:

        context = self._context_builder.build(
            memory=memory,
            role=role,
            seniority=seniority,
            area=area,
            question_count=question_count,
        )

        return self.retrieve_questions(
            query=query,
            context=context,
        )

    # =====================================================
    # PUBLIC — VECTOR SEARCH
    # =====================================================

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> list[RetrievalCandidate]:

        return self._chroma_retrieval_service.search(
            query=query,
            k=k,
        )

    def search_with_filters(
        self,
        query: str,
        filters: RetrievalFilters,
        k: int = 5,
    ) -> list[RetrievalCandidate]:

        return self._chroma_retrieval_service.search_with_filters(
            query=query,
            filters=filters,
            k=k,
        )
