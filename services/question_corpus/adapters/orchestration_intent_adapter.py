# services/question_corpus/adapters/orchestration_intent_adapter.py

from domain.contracts.user.role import RoleType

from services.retrieval.contracts.retrieval_planning_intent import RetrievalPlanningIntent
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.adaptive_context_builder import (
    AdaptiveContextBuilder,
)


class OrchestrationIntentAdapter:

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
        intent: RetrievalPlanningIntent,
        role: RoleType,
        target_area: str,
        memory: InterviewRetrievalMemory | None = None,
    ) -> AdaptiveRetrievalContext:

        safe_memory = memory if memory is not None else InterviewRetrievalMemory()

        return self._context_builder.build(
            memory=safe_memory,
            role=role.value,
            seniority=intent.target_level,
            area=target_area,
            question_count=intent.max_candidates,
        )
