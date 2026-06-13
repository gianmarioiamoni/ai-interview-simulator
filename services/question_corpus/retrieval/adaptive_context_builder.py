# services/question_corpus/retrieval/adaptive_context_builder.py

from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory
from infrastructure.config.evaluation import (
    ADAPTIVE_DIFFICULTY_HIGH,
    ADAPTIVE_DIFFICULTY_HIGH_SCORE,
    ADAPTIVE_DIFFICULTY_MEDIUM,
    ADAPTIVE_DIFFICULTY_MEDIUM_SCORE,
    ADAPTIVE_DIFFICULTY_BASE,
)



class AdaptiveContextBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        memory: InterviewRetrievalMemory,
        role: str,
        seniority: str,
        area: str,
        question_count: int,
        retrieval_query: str | None = None,
    ) -> AdaptiveRetrievalContext:

        target_difficulty = self._compute_target_difficulty(
            memory,
        )

        return AdaptiveRetrievalContext(
            current_role=role,
            seniority=seniority,
            target_area=area,
            target_question_count=question_count,
            already_used_domains=memory.covered_domains,
            weak_domains=memory.weak_domains,
            strong_domains=memory.strong_domains,
            target_difficulty=target_difficulty,
            retrieval_query=retrieval_query,
            memory=memory,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _compute_target_difficulty(
        self,
        memory: InterviewRetrievalMemory,
    ) -> int:

        if memory.average_score >= ADAPTIVE_DIFFICULTY_HIGH_SCORE:
            return ADAPTIVE_DIFFICULTY_HIGH

        if memory.average_score >= ADAPTIVE_DIFFICULTY_MEDIUM_SCORE:
            return ADAPTIVE_DIFFICULTY_MEDIUM

        return ADAPTIVE_DIFFICULTY_BASE
