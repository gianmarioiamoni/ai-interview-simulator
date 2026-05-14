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

from services.question_intelligence.area_question_builder import (
    AreaQuestionBuilder,
)

from services.question_intelligence.quality.question_set_quality_analyzer import (
    QuestionSetQualityAnalyzer,
)

from app.settings.constants import QUESTIONS_PER_AREA

logger = logging.getLogger(__name__)


class QuestionSetBuilder:
    def __init__(
        self,
        area_builder: AreaQuestionBuilder,
        deduplicator: SemanticDeduplicator,
        quality_analyzer: QuestionSetQualityAnalyzer,
    ) -> None:
        self._area_builder = area_builder
        self._deduplicator = deduplicator
        self._quality_analyzer = quality_analyzer

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

            area_questions = self._area_builder.build(
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

                new_questions = self._area_builder.build(
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

        quality_report = self._quality_analyzer.analyze(all_questions)

        logger.info(
            f"[QUALITY] "
            f"avg_similarity={quality_report.similarity.average_similarity:.2f} "
            f"max_similarity={quality_report.similarity.max_similarity:.2f} "
            f"duplicates={quality_report.similarity.duplicate_pairs} "
            f"diversity={quality_report.diversity.diversity_score:.2f}"
            f"area_coverage={quality_report.coverage.area_coverage_score:.2f} "
            f"difficulty_balance={quality_report.coverage.difficulty_balance_score:.2f}"
        )

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
