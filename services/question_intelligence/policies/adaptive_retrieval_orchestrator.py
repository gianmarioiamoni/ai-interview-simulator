# services/question_intelligence/policies/adaptive_retrieval_orchestrator.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.reranking.coverage_constrained_reranker import (
    CoverageConstrainedReranker,
)

from services.question_intelligence.policies.retrieval_policy_resolver import (
    RetrievalPolicyResolver,
)


class AdaptiveRetrievalOrchestrator:

    def __init__(self) -> None:

        self._policy_resolver = RetrievalPolicyResolver()

        self._reranker = CoverageConstrainedReranker()

    # =====================================================
    # PUBLIC
    # =====================================================

    def optimize(
        self,
        items: List[QuestionBankItem],
        role: RoleType,
        level: SeniorityLevel,
        target_count: int,
    ):

        policy = self._policy_resolver.resolve(
            role=role,
            level=level,
        )

        return self._reranker.rerank(
            items=items,
            target_count=target_count,
            max_per_topic=(policy.max_questions_per_topic),
        )
