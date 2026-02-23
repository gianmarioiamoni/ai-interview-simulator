# services/question_intelligence/question_set_builder.py

# QuestionSetBuilder
#
# Responsibility:
# Builds the full interview question set (20 questions total).
# Ensures structural integrity and coherence.

from typing import List

from domain.contracts.question import Question
from services.question_intelligence.question_selection_service import (
    QuestionSelectionService,
)


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
    ) -> List[Question]:

        all_questions: List[Question] = []

        for area in areas:
            area_questions = self._selection_service.build_area_questions(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
            )

            if len(area_questions) != 4:
                raise ValueError(f"Area {area} did not produce exactly 4 questions")

            all_questions.extend(area_questions)

        if len(all_questions) != 20:
            raise ValueError(f"Expected 20 questions, got {len(all_questions)}")

        self._validate_no_duplicates(all_questions)

        return all_questions

    def _validate_no_duplicates(self, questions: List[Question]) -> None:
        prompts = [q.prompt.strip().lower() for q in questions]

        if len(prompts) != len(set(prompts)):
            raise ValueError("Duplicate questions detected in final set")
