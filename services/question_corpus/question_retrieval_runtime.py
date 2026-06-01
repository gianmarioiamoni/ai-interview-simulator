# services/question_corpus/question_retrieval_runtime.py

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.adaptive_retrieval_service import (
    AdaptiveRetrievalService,
)


class QuestionRetrievalRuntime:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        adaptive_retrieval_service: AdaptiveRetrievalService | None = None,
    ) -> None:

        self._adaptive_retrieval_service = (
            adaptive_retrieval_service
            if adaptive_retrieval_service is not None
            else AdaptiveRetrievalService()
        )

    # =====================================================
    # PUBLIC
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
