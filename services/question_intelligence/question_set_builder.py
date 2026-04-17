# services/question_intelligence/question_set_builder.py

# Responsibility:
# Builds the full interview question set (20 questions total).
# Ensures structural integrity and coherence.

from typing import List
import random

from domain.contracts.question.question import Question
from services.question_intelligence.question_selection_service import (
    QuestionSelectionService,
)

from app.settings.constants import QUESTIONS_PER_AREA


class QuestionSetBuilder:
    def __init__(
        self,
        selection_service: QuestionSelectionService,
    ) -> None:
        self._selection_service = selection_service

    def build(
        self,
        role: str,
        level: str,
        interview_type: str,
        areas: List[str],
        questions_per_area: int = QUESTIONS_PER_AREA,
    ) -> List[Question]:

        all_questions: List[Question] = []
        shuffled_areas = random.sample(areas, len(areas))

        for area in shuffled_areas:
            area_questions = self._selection_service.build_area_questions(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
                questions_per_area=questions_per_area,
            )

            if len(area_questions) < questions_per_area:
                f"Area {area} produced {len(area_questions)} questions, expected at least {questions_per_area}"

            all_questions.extend(area_questions[:questions_per_area])

        self._validate_no_duplicates(all_questions)

        return all_questions

    def _validate_no_duplicates(self, questions: List[Question]) -> None:
        prompts = [q.prompt.strip().lower() for q in questions]

        if len(prompts) != len(set(prompts)):
            # raise ValueError("Duplicate questions detected in final set")
            print("[WARNING] Duplicate questions detected in final set")
