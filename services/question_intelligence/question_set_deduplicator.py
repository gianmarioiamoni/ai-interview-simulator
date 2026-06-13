# services/question_intelligence/question_set_deduplicator.py

from typing import List

from domain.contracts.question.question import Question
from domain.contracts.interview.interview_area import InterviewArea

from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator
from services.question_intelligence.question_set_coding_dedup import (
    prioritize_corpus_coding_for_dedup,
)
from services.question_intelligence.question_set_knowledge_dedup import (
    prioritize_technical_knowledge_for_dedup,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class QuestionSetDeduplicator:
    """
    Removes exact and semantic duplicate questions from a question set.

    Responsibilities:
    - Exact duplicate removal (by normalised prompt)
    - Area-aware semantic deduplication via SemanticDeduplicator
    - Area-specific priority pre-sorting (coding, technical-knowledge)
    - Refill area ordering (technical-knowledge first)
    - Post-assembly duplicate validation
    """

    def __init__(self, deduplicator: SemanticDeduplicator) -> None:
        self._deduplicator = deduplicator

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def deduplicate(self, questions: List[Question]) -> List[Question]:
        """Remove exact duplicates then apply per-area semantic deduplication."""

        questions = self._remove_exact_duplicates(questions)

        if not questions:
            return questions

        area_order: list[InterviewArea] = []
        for question in questions:
            if question.area not in area_order:
                area_order.append(question.area)

        deduped: List[Question] = []

        for area in area_order:
            area_questions = [q for q in questions if q.area == area]

            if area == InterviewArea.TECH_TECHNICAL_KNOWLEDGE:
                area_questions = prioritize_technical_knowledge_for_dedup(area_questions)
            elif area == InterviewArea.TECH_CODING:
                area_questions = prioritize_corpus_coding_for_dedup(area_questions)

            deduped.extend(self._deduplicator.deduplicate(area_questions))

        return deduped

    def refill_area_order(self, areas: List[InterviewArea]) -> List[InterviewArea]:
        """Return areas reordered so technical-knowledge is filled first."""

        knowledge = InterviewArea.TECH_TECHNICAL_KNOWLEDGE
        prioritized = [a for a in areas if a == knowledge]
        prioritized.extend(a for a in areas if a != knowledge)
        return prioritized

    def validate_no_duplicates(self, questions: List[Question]) -> None:
        """Log a warning if duplicate prompts are detected."""

        prompts = [q.prompt.strip().lower() for q in questions]

        if len(prompts) != len(set(prompts)):
            logger.warning("[QuestionSetDeduplicator] Duplicate questions detected after assembly")

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    def _remove_exact_duplicates(self, questions: List[Question]) -> List[Question]:

        seen: set[str] = set()
        unique: List[Question] = []

        for q in questions:
            key = q.prompt.strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(q)

        return unique
