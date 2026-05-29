# services/question_corpus/retrieval/weak_domain_boost_engine.py

from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate


class WeakDomainBoostEngine:

    # =====================================================
    # CONSTANTS
    # =====================================================

    DOMAIN_BOOST = 0.10

    # =====================================================
    # PUBLIC
    # =====================================================

    def apply(
        self,
        candidates: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalCandidate]:

        boosted: list[RetrievalCandidate] = []

        weak_domains = set(
            context.weak_domains,
        )

        for candidate in candidates:

            domains = self._extract_domains(
                candidate,
            )

            overlap = weak_domains.intersection(
                domains,
            )

            boost = len(overlap) * self.DOMAIN_BOOST

            updated = candidate.model_copy(
                update={
                    "adaptive_score": round(
                        candidate.adaptive_score + boost,
                        3,
                    )
                }
            )

            boosted.append(
                updated,
            )

        boosted.sort(
            key=lambda c: c.adaptive_score,
            reverse=True,
        )

        return boosted

    # =====================================================
    # INTERNALS
    # =====================================================

    def _extract_domains(
        self,
        candidate: RetrievalCandidate,
    ) -> list[str]:

        domains = candidate.document.metadata.get(
            "domains",
            "",
        )

        if not domains:
            return []

        return [d.strip() for d in domains.split(",")]
