# services/question_corpus/retrieval/coverage_penalty_engine.py

from domain.contracts.question.sql_domain import SqlDomain
from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.utils.domain_parser import parse_sql_domains


class CoveragePenaltyEngine:

    # =====================================================
    # CONSTANTS
    # =====================================================

    DOMAIN_REPEAT_PENALTY = 0.15

    # =====================================================
    # PUBLIC
    # =====================================================

    def apply(
        self,
        candidates: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalCandidate]:

        adjusted: list[RetrievalCandidate] = []

        used_domains = set(
            context.already_used_domains,
        )

        for candidate in candidates:

            candidate_domains = self._extract_domains(
                candidate,
            )

            overlap = used_domains.intersection(
                candidate_domains,
            )

            penalty = len(overlap) * self.DOMAIN_REPEAT_PENALTY

            adjusted_score = max(
                0.0,
                candidate.adaptive_score - penalty,
            )

            adjusted_candidate = candidate.model_copy(
                update={
                    "adaptive_score": round(
                        adjusted_score,
                        3,
                    )
                }
            )

            adjusted.append(
                adjusted_candidate,
            )

        adjusted.sort(
            key=lambda c: c.adaptive_score,
            reverse=True,
        )

        return adjusted

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
