# services/question_intelligence/retrieval/retrieval_strategy_resolver.py

from domain.contracts.interview.interview_area import (
    InterviewArea,
)
from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.retrieval.retrieval_strategy import (
    RetrievalStrategy,
)


class RetrievalStrategyResolver:

    def resolve(
        self,
        area: InterviewArea,
        level: SeniorityLevel,
        questions_per_area: int,
    ) -> RetrievalStrategy:

        # -------------------------------------------------
        # BASE
        # -------------------------------------------------

        fetch_multiplier = 4
        lambda_mult = 0.5

        # -------------------------------------------------
        # AREA ADAPTATION
        # -------------------------------------------------

        if area == InterviewArea.TECH_CODING:
            # maximize diversity
            fetch_multiplier = 6
            lambda_mult = 0.25

        elif area == InterviewArea.TECH_DATABASE:
            # prioritize semantic precision
            fetch_multiplier = 4
            lambda_mult = 0.7

        # -------------------------------------------------
        # LEVEL ADAPTATION
        # -------------------------------------------------

        if level == SeniorityLevel.JUNIOR:
            # narrower retrieval
            fetch_multiplier = max(fetch_multiplier - 1, 2)

        elif level == SeniorityLevel.SENIOR:
            # broader conceptual retrieval
            fetch_multiplier += 2

        # -------------------------------------------------
        # FINAL STRATEGY
        # -------------------------------------------------

        return RetrievalStrategy(
            k=questions_per_area,
            fetch_k=questions_per_area * fetch_multiplier,
            use_mmr=True,
            lambda_mult=lambda_mult,
        )
