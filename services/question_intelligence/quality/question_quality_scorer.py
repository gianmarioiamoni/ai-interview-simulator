# services/question_intelligence/quality/question_quality_scorer.py

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.quality.quality_score_breakdown import (
    QualityScoreBreakdown,
)

from services.question_intelligence.quality.scored_question import (
    ScoredQuestion,
)


class QuestionQualityScorer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def score(
        self,
        item: QuestionBankItem,
        level: SeniorityLevel,
    ) -> ScoredQuestion:

        practical = self._score_practical_relevance(
            item.text,
        )

        production = self._score_production_relevance(
            item.text,
        )

        architectural = self._score_architectural_depth(
            item.text,
        )

        ambiguity_penalty = self._score_ambiguity_penalty(
            item.text,
        )

        seniority = self._score_seniority_alignment(
            item.text,
            level,
        )

        final_score = (
            practical * 0.25
            + production * 0.25
            + architectural * 0.25
            + seniority * 0.25
            - ambiguity_penalty
        )

        breakdown = QualityScoreBreakdown(
            practical_relevance=round(
                practical,
                2,
            ),
            production_relevance=round(
                production,
                2,
            ),
            architectural_depth=round(
                architectural,
                2,
            ),
            ambiguity_penalty=round(
                ambiguity_penalty,
                2,
            ),
            seniority_alignment=round(
                seniority,
                2,
            ),
            final_score=round(
                max(final_score, 0),
                2,
            ),
        )

        return ScoredQuestion(
            item=item,
            breakdown=breakdown,
        )

    # =====================================================
    # PRACTICAL
    # =====================================================

    def _score_practical_relevance(
        self,
        text: str,
    ) -> float:

        lower = text.lower()

        strong_terms = [
            "optimize",
            "scalability",
            "distributed",
            "performance",
            "production",
            "concurrency",
        ]

        score = 0.3

        for term in strong_terms:

            if term in lower:
                score += 0.15

        return min(score, 1.0)

    # =====================================================
    # PRODUCTION
    # =====================================================

    def _score_production_relevance(
        self,
        text: str,
    ) -> float:

        lower = text.lower()

        production_terms = [
            "production",
            "high concurrency",
            "optimization",
            "distributed",
            "transactions",
            "sharding",
        ]

        score = 0.2

        for term in production_terms:

            if term in lower:
                score += 0.2

        return min(score, 1.0)

    # =====================================================
    # ARCHITECTURE
    # =====================================================

    def _score_architectural_depth(
        self,
        text: str,
    ) -> float:

        lower = text.lower()

        architecture_terms = [
            "distributed",
            "scalability",
            "architecture",
            "trade-off",
            "system design",
            "sharding",
        ]

        score = 0.2

        for term in architecture_terms:

            if term in lower:
                score += 0.2

        return min(score, 1.0)

    # =====================================================
    # AMBIGUITY
    # =====================================================

    def _score_ambiguity_penalty(
        self,
        text: str,
    ) -> float:

        lower = text.lower()

        vague_terms = [
            "what is",
            "define",
            "explain briefly",
        ]

        penalty = 0.0

        for term in vague_terms:

            if term in lower:
                penalty += 0.1

        return min(penalty, 0.5)

    # =====================================================
    # SENIORITY
    # =====================================================

    def _score_seniority_alignment(
        self,
        text: str,
        level: SeniorityLevel,
    ) -> float:

        lower = text.lower()

        advanced_terms = [
            "distributed",
            "optimization",
            "scalability",
            "performance",
            "concurrency",
            "trade-off",
        ]

        advanced_count = sum(term in lower for term in advanced_terms)

        if level == SeniorityLevel.SENIOR:

            return min(
                0.3 + advanced_count * 0.15,
                1.0,
            )

        if level == SeniorityLevel.JUNIOR:

            if advanced_count > 2:
                return 0.3

            return 0.9

        return 0.7
