# services/question_corpus/retrieval/adaptive_retrieval_service.py

from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.chroma_retrieval_service import ChromaRetrievalService
from services.question_corpus.retrieval.adaptive_retrieval_policy import AdaptiveRetrievalPolicy
from services.question_corpus.retrieval.coverage_penalty_engine import CoveragePenaltyEngine
from services.question_corpus.retrieval.weak_domain_boost_engine import WeakDomainBoostEngine


class AdaptiveRetrievalService:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._retrieval = ChromaRetrievalService()

        self._policy = AdaptiveRetrievalPolicy()

        self._coverage_engine = CoveragePenaltyEngine()

        self._weak_domain_engine = WeakDomainBoostEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def retrieve(
        self,
        query: str,
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalCandidate]:

        filters = self._policy.build_filters(
            context,
        )

        candidates = self._retrieval.search_with_filters(
            query=query,
            filters=filters,
            k=context.target_question_count * 3,
        )

        adjusted = self._coverage_engine.apply(
            candidates=candidates,
            context=context,
        )

        adjusted = self._weak_domain_engine.apply(
            candidates=adjusted,
            context=context,
        )

        return adjusted[: context.target_question_count]
