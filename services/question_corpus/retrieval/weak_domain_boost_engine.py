# services/question_corpus/retrieval/weak_domain_boost_engine.py

from domain.contracts.question.sql_domain import SqlDomain
from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.utils.domain_parser import parse_sql_domains
from services.question_intelligence.interview_theme_memory import get_interview_theme_anchor


class WeakDomainBoostEngine:

    # =====================================================
    # CONSTANTS
    # =====================================================

    DOMAIN_BOOST = 0.10
    THEME_AFFINITY_BOOST = 0.08

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

        theme_anchor = get_interview_theme_anchor(
            context.memory,
        )

        for candidate in candidates:

            domains = self._extract_domains(
                candidate,
            )

            overlap = weak_domains.intersection(
                domains,
            )

            boost = len(overlap) * self.DOMAIN_BOOST

            if theme_anchor:
                boost += self._theme_affinity_boost(
                    candidate=candidate,
                    domains=domains,
                    theme_anchor=theme_anchor,
                )

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
    ) -> list[SqlDomain]:

        return parse_sql_domains(
            candidate.document.metadata.get("domains"),
        )

    def _theme_affinity_boost(
        self,
        candidate: RetrievalCandidate,
        domains: list[SqlDomain],
        theme_anchor: str,
    ) -> float:

        domain_values = [d.value for d in domains]

        if theme_anchor in domain_values:
            return self.THEME_AFFINITY_BOOST

        readable_theme = theme_anchor.replace("_", " ")
        lower_text = candidate.document.page_content.lower()

        if theme_anchor in lower_text or readable_theme in lower_text:
            return self.THEME_AFFINITY_BOOST * 0.5

        return 0.0
