# services/question_intelligence/question_set_builder.py

# Responsibility:
# Builds the full interview question set (20 questions total).
# Ensures structural integrity and coherence.

from typing import List
import random
import logging

from domain.contracts.question.question import Question
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator
from services.question_intelligence.question_selection_service import (
    QuestionSelectionService,
)

from app.settings.constants import QUESTIONS_PER_AREA

logger = logging.getLogger(__name__)


class QuestionSetBuilder:
    def __init__(
        self,
        selection_service: QuestionSelectionService,
        deduplicator: SemanticDeduplicator,
    ) -> None:
        self._selection_service = selection_service
        self._deduplicator = deduplicator

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        areas: List[InterviewArea],
        questions_per_area: int = QUESTIONS_PER_AREA,
    ) -> List[Question]:

        print(type(areas[0]), areas[0])

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
                logger.warning(f"Area {area} produced {len(area_questions)} questions, expected at least {questions_per_area}")

            all_questions.extend(area_questions[:questions_per_area])

        all_questions = self._deduplicator.deduplicate(all_questions)

        self._validate_no_duplicates(all_questions)

        return all_questions

    def _validate_no_duplicates(self, questions: List[Question]) -> None:
        prompts = [q.prompt.strip().lower() for q in questions]

        if len(prompts) != len(set(prompts)):
            # raise ValueError("Duplicate questions detected in final set")
            print("[WARNING] Duplicate questions detected in final set")
