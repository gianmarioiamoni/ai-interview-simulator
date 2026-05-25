# services/replanning/retrieval_recovery_service.py

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.interview_orchestration.orchestration_intent_builder import OrchestrationIntentBuilder
from services.replanning.role_expansion_strategy import RoleExpansionStrategy
from services.retrieval.memory_aware_retrieval_pipeline import MemoryAwareRetrievalPipeline
from services.retrieval.planner_retrieval_service import PlannerRetrievalService
from services.retrieval.retrieval_runtime_mapper import RetrievalRuntimeMapper
from services.retrieval.retrieval_session_memory import RetrievalSessionMemory


class RetrievalRecoveryService:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._role_strategy = RoleExpansionStrategy()

        self._intent_builder = OrchestrationIntentBuilder()

        self._retrieval_service = PlannerRetrievalService()

        self._runtime_mapper = RetrievalRuntimeMapper()

        self._retrieval_pipeline = MemoryAwareRetrievalPipeline(
            memory=RetrievalSessionMemory(),
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def expand_role_scope(
        self,
        items: list[QuestionBankItem],
        role: RoleType,
        level: SeniorityLevel,
    ) -> list[QuestionBankItem]:

        expanded_roles = self._role_strategy.expand(
            role=role,
        )

        expanded_questions: list[QuestionBankItem] = []

        for expanded_role in expanded_roles:

            intent = self._intent_builder.build(
                role=expanded_role,
                level=level,
            )

            symbolic_results = self._retrieval_service.retrieve_candidates(
                intent=intent,
                corpus_path="datasets/curated/tech_interview_handbook.json",
            )

            retrieval_results = self._retrieval_pipeline.process(
                results=symbolic_results,
            )

            records = [result.symbolic_result.record for result in retrieval_results]

            mapped = self._runtime_mapper.map(
                records=records,
            )

            expanded_questions.extend(mapped)

        return self._deduplicate(
            original=items,
            expanded=expanded_questions,
        )

    # =====================================================
    # DEDUPLICATION
    # =====================================================

    def _deduplicate(
        self,
        original: list[QuestionBankItem],
        expanded: list[QuestionBankItem],
    ) -> list[QuestionBankItem]:

        seen_ids = {item.id for item in original}

        merged = list(original)

        for item in expanded:

            if item.id in seen_ids:
                continue

            seen_ids.add(item.id)

            merged.append(item)

        return merged
