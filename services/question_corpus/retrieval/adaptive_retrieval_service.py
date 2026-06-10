# services/question_corpus/retrieval/adaptive_retrieval_service.py
#
# Internal implementation detail. External callers must use
# QuestionRetrievalRuntime instead of importing this module directly.

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.retrieval.chroma_retrieval_service import ChromaRetrievalService
from services.question_corpus.retrieval.adaptive_retrieval_policy import AdaptiveRetrievalPolicy
from services.question_corpus.retrieval.coverage_penalty_engine import CoveragePenaltyEngine
from services.question_corpus.retrieval.weak_domain_boost_engine import WeakDomainBoostEngine
from services.question_corpus.retrieval.question_repetition_filter import QuestionRepetitionFilter
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)

BACKGROUND_MIN_POOL_AREA = "technical_background"

MIN_FRESH_START_POOL_SIZE = 5


class AdaptiveRetrievalService:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        retrieval: ChromaRetrievalService | None = None,
        policy: AdaptiveRetrievalPolicy | None = None,
        coverage_engine: CoveragePenaltyEngine | None = None,
        weak_domain_engine: WeakDomainBoostEngine | None = None,
        repetition_filter: QuestionRepetitionFilter | None = None,
        performance_selector: PerformanceResponsiveCandidateSelector | None = None,
    ) -> None:

        self._retrieval = (
            retrieval if retrieval is not None else ChromaRetrievalService()
        )

        self._policy = policy if policy is not None else AdaptiveRetrievalPolicy()

        self._coverage_engine = (
            coverage_engine if coverage_engine is not None else CoveragePenaltyEngine()
        )

        self._weak_domain_engine = (
            weak_domain_engine
            if weak_domain_engine is not None
            else WeakDomainBoostEngine()
        )

        self._repetition_filter = (
            repetition_filter
            if repetition_filter is not None
            else QuestionRepetitionFilter()
        )

        self._performance_selector = (
            performance_selector
            if performance_selector is not None
            else PerformanceResponsiveCandidateSelector()
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def retrieve(
        self,
        query: str,
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalCandidate]:

        filter_stages = self._policy.build_relaxation_stages(
            context,
        )

        fetch_k = context.target_question_count * 3

        candidates = self._retrieve_with_staged_filters(
            query=query,
            filter_stages=filter_stages,
            fetch_k=fetch_k,
            memory=context.memory,
            min_pool_size=self._min_pool_size(context),
        )

        if not candidates:
            return []

        adjusted = self._coverage_engine.apply(
            candidates=candidates,
            context=context,
        )

        adjusted = self._weak_domain_engine.apply(
            candidates=adjusted,
            context=context,
        )

        adjusted.sort(
            key=lambda c: c.adaptive_score or c.final_score,
            reverse=True,
        )

        return self._performance_selector.select(
            pool=adjusted,
            context=context,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _retrieve_with_staged_filters(
        self,
        query: str,
        filter_stages: list[RetrievalFilters],
        fetch_k: int,
        memory: InterviewRetrievalMemory,
        min_pool_size: int = 1,
    ) -> list[RetrievalCandidate]:

        best_undersized: list[RetrievalCandidate] = []

        for stage_filters in filter_stages:

            stage_candidates = self._retrieval.search_with_filters(
                query=query,
                filters=stage_filters,
                k=fetch_k,
            )

            filtered = self._repetition_filter.apply(
                candidates=stage_candidates,
                memory=memory,
            )

            if len(filtered) >= min_pool_size:
                return filtered

            if len(filtered) > len(best_undersized):
                best_undersized = filtered

        return best_undersized

    def _min_pool_size(
        self,
        context: AdaptiveRetrievalContext,
    ) -> int:

        if context.target_area != BACKGROUND_MIN_POOL_AREA:
            return 1

        if not self._is_fresh_start(context):
            return 1

        return MIN_FRESH_START_POOL_SIZE

    def _is_fresh_start(
        self,
        context: AdaptiveRetrievalContext,
    ) -> bool:

        if context.already_used_question_ids:
            return False

        memory = context.memory

        return (
            not memory.asked_question_ids
            and not memory.session_selected_prompts
            and not memory.session_used_topics
            and not memory.difficulty_history
        )
