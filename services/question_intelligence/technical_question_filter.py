# services/question_intelligence/technical_question_filter.py

import re

from services.question_intelligence.quality.contracts import TechnicalFilterResult
from services.question_intelligence.quality.technical_taxonomy import TechnicalTaxonomy


class TechnicalQuestionFilter:
    """
    Classifies a question text as technical or non-technical using
    TechnicalTaxonomy term sets.

    Public API
    ----------
    evaluate(text) -> TechnicalFilterResult
    is_technical(text) -> bool
    matching_categories(text) -> list[str]
    """

    # ------------------------------------------------------------------
    # Class-level aliases preserved for any consumer that references them
    # directly on the class (e.g. TechnicalQuestionFilter.STRONG_BACKEND_TERMS).
    # ------------------------------------------------------------------

    STRONG_BACKEND_TERMS = TechnicalTaxonomy.STRONG_BACKEND_TERMS
    WEAK_BACKEND_TERMS = TechnicalTaxonomy.WEAK_BACKEND_TERMS
    STRONG_DATABASE_TERMS = TechnicalTaxonomy.STRONG_DATABASE_TERMS
    WEAK_DATABASE_TERMS = TechnicalTaxonomy.WEAK_DATABASE_TERMS
    STRONG_DISTRIBUTED_TERMS = TechnicalTaxonomy.STRONG_DISTRIBUTED_TERMS
    WEAK_DISTRIBUTED_TERMS = TechnicalTaxonomy.WEAK_DISTRIBUTED_TERMS
    STRONG_FRONTEND_TERMS = TechnicalTaxonomy.STRONG_FRONTEND_TERMS
    WEAK_FRONTEND_TERMS = TechnicalTaxonomy.WEAK_FRONTEND_TERMS
    STRONG_DEVOPS_TERMS = TechnicalTaxonomy.STRONG_DEVOPS_TERMS
    WEAK_DEVOPS_TERMS = TechnicalTaxonomy.WEAK_DEVOPS_TERMS
    STRONG_DATA_ENGINEERING_TERMS = TechnicalTaxonomy.STRONG_DATA_ENGINEERING_TERMS
    WEAK_DATA_ENGINEERING_TERMS = TechnicalTaxonomy.WEAK_DATA_ENGINEERING_TERMS
    STRONG_ML_TERMS = TechnicalTaxonomy.STRONG_ML_TERMS
    WEAK_ML_TERMS = TechnicalTaxonomy.WEAK_ML_TERMS
    STRONG_CS_TERMS = TechnicalTaxonomy.STRONG_CS_TERMS
    WEAK_CS_TERMS = TechnicalTaxonomy.WEAK_CS_TERMS

    CATEGORY_MAP = TechnicalTaxonomy.CATEGORY_MAP

    # =====================================================
    # PUBLIC
    # =====================================================

    def evaluate(
        self,
        text: str,
    ) -> TechnicalFilterResult:

        normalized = self._normalize_text(text)

        matched_categories: list[str] = []

        matched_terms: list[str] = []

        all_strong_matches: list[str] = []

        all_weak_matches: list[str] = []

        score = 0.0

        # -------------------------------------------------
        # CATEGORY MATCHING
        # -------------------------------------------------

        for (
            category,
            (
                strong_terms,
                weak_terms,
            ),
        ) in self.CATEGORY_MAP.items():

            (
                is_match,
                strong_matches,
                weak_matches,
            ) = self._category_matches(
                normalized_text=normalized,
                strong_terms=strong_terms,
                weak_terms=weak_terms,
            )

            if not is_match:
                continue

            matched_categories.append(category)

            matched_terms.extend(strong_matches)
            matched_terms.extend(weak_matches)

            all_strong_matches.extend(strong_matches)
            all_weak_matches.extend(weak_matches)

            # -------------------------------------------------
            # WEIGHTED SCORING
            # -------------------------------------------------

            score += len(strong_matches) * 0.25
            score += len(weak_matches) * 0.08

        # -------------------------------------------------
        # MULTI-DOMAIN BONUS
        # -------------------------------------------------

        if len(matched_categories) >= 2:
            score += 0.15

        if len(matched_categories) >= 3:
            score += 0.10

        # -------------------------------------------------
        # FINAL NORMALIZATION
        # -------------------------------------------------

        score = min(score, 1.0)

        matched_terms = sorted(list(set(matched_terms)))

        matched_categories = sorted(list(set(matched_categories)))

        return TechnicalFilterResult(
            is_technical=(score >= 0.30),
            score=round(score, 2),
            matched_categories=matched_categories,
            matched_terms=matched_terms,
            strong_matches=sorted(list(set(all_strong_matches))),
            weak_matches=sorted(list(set(all_weak_matches))),
        )

    def is_technical(
        self,
        text: str,
    ) -> bool:

        result = self.evaluate(text)

        return result.is_technical

    def matching_categories(
        self,
        text: str,
    ) -> list[str]:

        normalized = self._normalize_text(text)

        categories: list[str] = []

        for (
            category,
            (
                strong_terms,
                weak_terms,
            ),
        ) in self.CATEGORY_MAP.items():

            (
                is_match,
                _strong,
                _weak,
            ) = self._category_matches(
                normalized_text=normalized,
                strong_terms=strong_terms,
                weak_terms=weak_terms,
            )

            if is_match:
                categories.append(category)

        return categories

    # =====================================================
    # HELPERS
    # =====================================================

    def _category_matches(
        self,
        normalized_text: str,
        strong_terms: frozenset[str] | set[str],
        weak_terms: frozenset[str] | set[str],
    ) -> tuple[bool, list[str], list[str]]:

        strong_matches = [
            term
            for term in strong_terms
            if self._contains_term(
                normalized_text,
                term,
            )
        ]

        weak_matches = [
            term
            for term in weak_terms
            if self._contains_term(
                normalized_text,
                term,
            )
        ]

        # -------------------------------------------------
        # MATCH RULES
        # -------------------------------------------------

        is_match = len(strong_matches) >= 1 or len(weak_matches) >= 2

        return (
            is_match,
            strong_matches,
            weak_matches,
        )

    def _contains_term(
        self,
        text: str,
        term: str,
    ) -> bool:

        normalized_text = self._normalize_text(text)

        normalized_term = self._normalize_text(term)

        pattern = r"\b" + re.escape(normalized_term) + r"\b"

        return (
            re.search(
                pattern,
                normalized_text,
            )
            is not None
        )

    def _normalize_text(
        self,
        text: str,
    ) -> str:

        normalized = text.lower()

        replacements = {
            "deadlocks": "deadlock",
            "mutexes": "mutex",
            "indexes": "index",
            "queries": "query",
            "pipelines": "pipeline",
            "transactions": "transaction",
            "deployments": "deployment",
            "systems": "system",
            "services": "service",
            "servers": "server",
        }

        for (
            source,
            target,
        ) in replacements.items():

            normalized = normalized.replace(
                source,
                target,
            )

        return normalized
