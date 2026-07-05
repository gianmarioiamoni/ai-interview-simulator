# services/question_intelligence/question_retrieval_service.py

# QuestionRetrievalService — executes semantic retrieval over the Question Bank.
# Retrieval backend is routed through question_corpus runtime.

from typing import List, Optional

from domain.contracts.question.question_bank_item import QuestionBankItem
from services.question_intelligence.adapters.retrieval_strategy_context_adapter import (
    RetrievalStrategyContextAdapter,
)
from services.question_intelligence.question_vector_store import QuestionVectorStore
from services.question_intelligence.retrieval.retrieval_strategy import RetrievalStrategy
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    RetrievalCandidateMapper,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.question_retrieval_runtime import QuestionRetrievalRuntime


class QuestionRetrievalService:

    def __init__(
        self,
        vector_store: QuestionVectorStore | None = None,
        context_adapter: RetrievalStrategyContextAdapter | None = None,
        question_retrieval_runtime: QuestionRetrievalRuntime | None = None,
        retrieval_candidate_mapper: RetrievalCandidateMapper | None = None,
    ) -> None:

        # vector_store accepted for API compatibility; not used by retrieve().
        self._vector_store = vector_store

        self._context_adapter = (
            context_adapter
            if context_adapter is not None
            else RetrievalStrategyContextAdapter()
        )

        self._question_retrieval_runtime = (
            question_retrieval_runtime
            if question_retrieval_runtime is not None
            else QuestionRetrievalRuntime()
        )

        self._retrieval_candidate_mapper = (
            retrieval_candidate_mapper
            if retrieval_candidate_mapper is not None
            else RetrievalCandidateMapper()
        )

    # =====================================================
    # PUBLIC API
    # =====================================================

    def retrieve(
        self,
        query: str,
        retrieval_strategy: RetrievalStrategy,
        role: Optional[str] = None,
        level: Optional[str] = None,
        interview_type: Optional[str] = None,
        area: Optional[str] = None,
        memory: InterviewRetrievalMemory | None = None,
    ) -> List[QuestionBankItem]:

        context = self._context_adapter.adapt(
            query=query,
            retrieval_strategy=retrieval_strategy,
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            memory=memory,
        )

        candidates = self._question_retrieval_runtime.retrieve_questions(
            query=query,
            context=context,
        )

        return self._retrieval_candidate_mapper.map(
            candidates=candidates,
        )
