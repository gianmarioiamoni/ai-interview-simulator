# services/question_intelligence/question_set_builder.py

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

    # =========================================================
    # PUBLIC
    # =========================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        areas: List[InterviewArea],
        questions_per_area: int = QUESTIONS_PER_AREA,
    ) -> List[Question]:

        expected_total = len(areas) * questions_per_area

        all_questions: List[Question] = []

        # -----------------------------------------------------
        # INITIAL GENERATION
        # -----------------------------------------------------

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
                logger.warning(
                    f"[QuestionSetBuilder] Area {area.value} produced "
                    f"{len(area_questions)} questions (expected {questions_per_area})"
                )

            all_questions.extend(area_questions[:questions_per_area])

        # -----------------------------------------------------
        # DEDUP (INITIAL)
        # -----------------------------------------------------

        all_questions = self._remove_exact_duplicates(all_questions)
        all_questions = self._deduplicator.deduplicate(all_questions)

        # -----------------------------------------------------
        # REFILL LOOP (STEP 2.4)
        # -----------------------------------------------------

        max_attempts = 3
        attempt = 0

        while len(all_questions) < expected_total and attempt < max_attempts:

            missing = expected_total - len(all_questions)

            logger.info(
                f"[QuestionSetBuilder] Refill attempt {attempt+1} → missing {missing}"
            )

            for area in areas:

                if missing <= 0:
                    break

                new_questions = self._selection_service.build_area_questions(
                    role=role,
                    level=level,
                    interview_type=interview_type,
                    area=area,
                    questions_per_area=1,
                )

                all_questions.extend(new_questions)
                missing -= len(new_questions)

            # re-dedup dopo refill
            all_questions = self._remove_exact_duplicates(all_questions)
            all_questions = self._deduplicator.deduplicate(all_questions)

            attempt += 1

        # -----------------------------------------------------
        # FINAL GUARD
        # -----------------------------------------------------

        if len(all_questions) < expected_total:
            logger.warning(
                f"[QuestionSetBuilder] Could not reach expected size "
                f"{expected_total}, got {len(all_questions)}"
            )

        # trimming finale (importante)
        all_questions = all_questions[:expected_total]

        # -----------------------------------------------------
        # FINAL VALIDATION
        # -----------------------------------------------------

        self._validate_no_duplicates(all_questions)

        return all_questions

    # =========================================================
    # HELPERS
    # =========================================================

    def _remove_exact_duplicates(self, questions: List[Question]) -> List[Question]:

        seen = set()
        unique: List[Question] = []

        for q in questions:
            key = q.prompt.strip().lower()

            if key not in seen:
                seen.add(key)
                unique.append(q)

        return unique

    def _validate_no_duplicates(self, questions: List[Question]) -> None:

        prompts = [q.prompt.strip().lower() for q in questions]

        if len(prompts) != len(set(prompts)):
            logger.warning("[QuestionSetBuilder] Duplicate questions still detected")
