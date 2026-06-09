# services/question_intelligence/adapters/retrieval_strategy_context_adapter.py

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.adaptive_context_builder import (
    AdaptiveContextBuilder,
)
from services.question_intelligence.retrieval.retrieval_strategy import (
    RetrievalStrategy,
)


class RetrievalStrategyContextAdapter:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        context_builder: AdaptiveContextBuilder | None = None,
    ) -> None:

        self._context_builder = (
            context_builder if context_builder is not None else AdaptiveContextBuilder()
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt(
        self,
        query: str,
        retrieval_strategy: RetrievalStrategy,
        role: str | None = None,
        level: str | None = None,
        interview_type: str | None = None,
        area: str | None = None,
        memory: InterviewRetrievalMemory | None = None,
    ) -> AdaptiveRetrievalContext:

        safe_memory = memory if memory is not None else InterviewRetrievalMemory()

        target_area = self._resolve_target_area(
            role=role,
            area=area,
        )

        return self._context_builder.build(
            memory=safe_memory,
            role=role or "backend_engineer",
            seniority=level or "mid",
            area=target_area,
            question_count=retrieval_strategy.k,
            retrieval_query=query,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _resolve_target_area(
        self,
        role: str | None,
        area: str | None,
    ) -> str:

        role_to_area = {
            "backend_engineer": "technical_case_study",
            "devops_engineer": "technical_technical_knowledge",
            "data_engineer": "technical_database",
            "frontend_engineer": "technical_technical_knowledge",
            "fullstack_engineer": "technical_case_study",
        }

        if area:
            return area

        if role and role in role_to_area:
            return role_to_area[role]

        return "technical_technical_knowledge"