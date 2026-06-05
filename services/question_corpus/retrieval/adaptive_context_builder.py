# services/question_corpus/retrieval/adaptive_context_builder.py

from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory



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
            memory=memory,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _compute_target_difficulty(
        self,
        memory: InterviewRetrievalMemory,
    ) -> int:

        if memory.average_score >= 0.85:
            return 5

        if memory.average_score >= 0.70:
            return 4

        return 3
