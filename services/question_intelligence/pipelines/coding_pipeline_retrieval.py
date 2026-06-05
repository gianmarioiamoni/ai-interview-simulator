# services/question_intelligence/pipelines/coding_pipeline_retrieval.py

from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    RetrievalCandidateMapper,
)
from services.question_corpus.retrieval.adaptive_retrieval_policy import (
    AdaptiveRetrievalPolicy,
)
from services.question_corpus.retrieval.chroma_retrieval_service import (
    ChromaRetrievalService,
)
from services.question_corpus.retrieval.coverage_penalty_engine import (
    CoveragePenaltyEngine,
)
from services.question_corpus.retrieval.question_repetition_filter import (
    QuestionRepetitionFilter,
)
from services.question_corpus.retrieval.weak_domain_boost_engine import (
    WeakDomainBoostEngine,
)
from services.question_intelligence.adapters.retrieval_strategy_context_adapter import (
    RetrievalStrategyContextAdapter,
)
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)
from services.question_intelligence.retrieval.retrieval_strategy import (
    RetrievalStrategy,
)

from domain.contracts.question.question_bank_item import QuestionBankItem
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

_CODING_MIN_CANDIDATE_POOL = 3


class CodingPipelineRetrievalHelper:

    """Coding-only retrieval: merge relaxation stages until the candidate pool is deep enough."""

    def __init__(
        self,
        context_adapter: RetrievalStrategyContextAdapter | None = None,
        policy: AdaptiveRetrievalPolicy | None = None,
        chroma_retrieval: ChromaRetrievalService | None = None,
        coverage_engine: CoveragePenaltyEngine | None = None,
        weak_domain_engine: WeakDomainBoostEngine | None = None,
        repetition_filter: QuestionRepetitionFilter | None = None,
        candidate_mapper: RetrievalCandidateMapper | None = None,
        performance_selector: PerformanceResponsiveCandidateSelector | None = None,
    ) -> None:

        self._context_adapter = (
            context_adapter
            if context_adapter is not None
            else RetrievalStrategyContextAdapter()
        )
        self._policy = policy if policy is not None else AdaptiveRetrievalPolicy()
        self._chroma = (
            chroma_retrieval
            if chroma_retrieval is not None
            else ChromaRetrievalService()
        )
        self._coverage_engine = (
            coverage_engine
            if coverage_engine is not None
            else CoveragePenaltyEngine()
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
        self._mapper = (
            candidate_mapper
            if candidate_mapper is not None
            else RetrievalCandidateMapper()
        )
        self._performance_selector = (
            performance_selector
            if performance_selector is not None
            else PerformanceResponsiveCandidateSelector()
        )

    def retrieve_candidates(
        self,
        query: str,
        retrieval_strategy: RetrievalStrategy,
        role: str,
        level: str,
        interview_type: str,
        area: str,
        memory: InterviewRetrievalMemory,
    ) -> list[QuestionBankItem]:

        context = self._context_adapter.adapt(
            query=query,
            retrieval_strategy=retrieval_strategy,
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            memory=memory,
        )

        filter_stages = self._policy.build_relaxation_stages(context)
        fetch_k = context.target_question_count * 3

        merged_pool: list[RetrievalCandidate] = []
        seen_document_ids: set[str] = set()

        for stage_filters in filter_stages:

            stage_candidates = self._chroma.search_with_filters(
                query=query,
                filters=stage_filters,
                k=fetch_k,
            )

            filtered = self._repetition_filter.apply(
                candidates=stage_candidates,
                memory=memory,
            )

            for candidate in filtered:
                document_id = candidate.document.metadata.get("document_id")

                if not document_id or document_id in seen_document_ids:
                    continue

                seen_document_ids.add(document_id)
                merged_pool.append(candidate)

            if len(merged_pool) >= _CODING_MIN_CANDIDATE_POOL:
                break

        if not merged_pool:
            return []

        adjusted = self._coverage_engine.apply(
            candidates=merged_pool,
            context=context,
        )

        adjusted = self._weak_domain_engine.apply(
            candidates=adjusted,
            context=context,
        )

        adjusted.sort(
            key=lambda candidate: candidate.adaptive_score or candidate.final_score,
            reverse=True,
        )

        prioritized = self._performance_selector.prioritize(
            pool=adjusted,
            context=context,
        )
        top_candidates = prioritized[: context.target_question_count]

        return self._mapper.map(candidates=top_candidates)


def retrieve_coding_candidates(
    retrieval_service: QuestionRetrievalService,
    query: str,
    retrieval_strategy: RetrievalStrategy,
    role: str,
    level: str,
    interview_type: str,
    area: str,
    memory: InterviewRetrievalMemory,
    coding_retrieval_helper: CodingPipelineRetrievalHelper | None = None,
) -> list[QuestionBankItem]:

    _ = retrieval_service

    helper = (
        coding_retrieval_helper
        if coding_retrieval_helper is not None
        else CodingPipelineRetrievalHelper()
    )

    return helper.retrieve_candidates(
        query=query,
        retrieval_strategy=retrieval_strategy,
        role=role,
        level=level,
        interview_type=interview_type,
        area=area,
        memory=memory,
    )
