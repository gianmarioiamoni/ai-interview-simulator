# services/replanning/retrieval_recovery_service.py

import time

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.interview_orchestration.orchestration_intent_builder import OrchestrationIntentBuilder
from services.replanning.role_expansion_strategy import RoleExpansionStrategy
from services.replanning.contracts.recovery_expansion_result import RecoveryExpansionResult
from services.replanning.contracts.retrieval_expansion_telemetry import RetrievalExpansionTelemetry
from services.question_corpus.adapters.orchestration_intent_adapter import (
    OrchestrationIntentAdapter,
)
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    RetrievalCandidateMapper,
)
from services.question_corpus.question_retrieval_runtime import QuestionRetrievalRuntime
from services.retrieval.memory_aware_retrieval_pipeline import MemoryAwareRetrievalPipeline
from services.retrieval.planner_retrieval_service import PlannerRetrievalService
from services.retrieval.retrieval_runtime_mapper import RetrievalRuntimeMapper
from services.retrieval.retrieval_session_memory import RetrievalSessionMemory
from services.planning_validation.recovery_action import RecoveryAction


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

        self._intent_adapter = OrchestrationIntentAdapter()

        self._question_retrieval_runtime = QuestionRetrievalRuntime()

        self._retrieval_candidate_mapper = RetrievalCandidateMapper()

    # =====================================================
    # PUBLIC
    # =====================================================

    def expand_role_scope(
        self,
        items: list[QuestionBankItem],
        role: RoleType,
        level: SeniorityLevel,
    ) -> RecoveryExpansionResult:

        start_time = time.perf_counter()

        expanded_roles = self._role_strategy.expand(
            role=role,
        )

        expanded_questions: list[QuestionBankItem] = []

        for expanded_role in expanded_roles:

            intent = self._intent_builder.build(
                role=expanded_role,
                level=level,
            )

            context = self._intent_adapter.adapt(
                intent=intent,
                role=expanded_role,
                target_area=self._resolve_target_area(
                    role=expanded_role,
                ),
            )

            candidates = self._question_retrieval_runtime.retrieve_questions(
                query=intent.query_text,
                context=context,
            )

            mapped = self._retrieval_candidate_mapper.map(
                candidates=candidates,
            )

            expanded_questions.extend(mapped)

        deduplicated = self._deduplicate(
            original=items,
            expanded=expanded_questions,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        telemetry = RetrievalExpansionTelemetry(
            original_role=role,
            expanded_roles=expanded_roles,
            recovered_candidates_count=max(
                0,
                len(deduplicated) - len(items),
            ),
            recovery_successful=(len(deduplicated) > len(items)),
            retrieval_duration_ms=round(
                duration_ms,
                2,
            ),
        )

        return RecoveryExpansionResult(
            expanded_items=deduplicated,
            applied_action=RecoveryAction.EXPAND_ROLE_SCOPE,
            added_candidates=max(
                0,
                len(deduplicated) - len(items),
            ),
            telemetry=telemetry,
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

    def _resolve_target_area(
        self,
        role: RoleType,
    ) -> str:

        role_to_area = {
            RoleType.BACKEND_ENGINEER: "technical_case_study",
            RoleType.DEVOPS_ENGINEER: "technical_technical_knowledge",
            RoleType.DATA_ENGINEER: "technical_database",
            RoleType.FRONTEND_ENGINEER: "technical_technical_knowledge",
            RoleType.FULLSTACK_ENGINEER: "technical_case_study",
        }

        return role_to_area.get(
            role,
            "technical_technical_knowledge",
        )
