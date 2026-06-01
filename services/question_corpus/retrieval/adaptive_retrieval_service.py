# services/question_corpus/retrieval/adaptive_retrieval_service.py
#
# Internal implementation detail. External callers must use
# QuestionRetrievalRuntime instead of importing this module directly.

from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.chroma_retrieval_service import ChromaRetrievalService
from services.question_corpus.retrieval.adaptive_retrieval_policy import AdaptiveRetrievalPolicy
from services.question_corpus.retrieval.coverage_penalty_engine import CoveragePenaltyEngine
from services.question_corpus.retrieval.weak_domain_boost_engine import WeakDomainBoostEngine
from services.question_corpus.retrieval.question_repetition_filter import QuestionRepetitionFilter


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

        self._repetition_filter = QuestionRepetitionFilter()

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

        print("\nAFTER RETRIEVAL\n")

        for c in candidates:

            print(c.document.metadata.get("document_id"))

        candidates = self._repetition_filter.apply(
            candidates=candidates,
            memory=context.memory,
        )

        print("\nAFTER REPETITION FILTER\n")

        for c in candidates:

            print(c.document.metadata.get("document_id"))

        if not candidates:

            candidates = self._retrieval.search(
                query=query,
                k=context.target_question_count * 5,
            )

        adjusted = self._coverage_engine.apply(
            candidates=candidates,
            context=context,
        )

        print("\nAFTER COVERAGE PENALTY\n")

        for c in adjusted:

            print(c.document.metadata.get("document_id"))

        adjusted = self._weak_domain_engine.apply(
            candidates=adjusted,
            context=context,
        )

        print("\nAFTER WEAK DOMAIN BOOST\n")

        for c in adjusted:

            print(c.document.metadata.get("document_id"))

        adjusted.sort(
            key=lambda c: c.adaptive_score,
            reverse=True,
        )

        return adjusted[: context.target_question_count]
