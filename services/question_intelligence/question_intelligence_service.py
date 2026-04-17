# services/question_intelligence/question_intelligence_service.py

# QuestionIntelligenceService
#
# Responsibility:
# Entry point for question generation.
# Orchestrates the construction of a full interview question set.
#
# This is a thin orchestration layer (Step 1).
# No business logic should live here.

from typing import List

from domain.contracts.question.question import Question
from services.question_intelligence.question_set_builder import (
    QuestionSetBuilder,
)

class QuestionIntelligenceService:
    def __init__(
        self,
        question_set_builder: QuestionSetBuilder,
    ) -> None:
        self._question_set_builder = question_set_builder

    # =========================================================
    # PUBLIC API
    # =========================================================

    def generate_interview_questions(
        self,
        role: str,
        level: str,
        interview_type: str,
        areas: List[str],
        questions_per_area: int = 1,
    ) -> List[Question]:

        return self._question_set_builder.build(
            role=role,
            level=level,
            interview_type=interview_type,
            areas=areas,
            questions_per_area=questions_per_area,
        )
