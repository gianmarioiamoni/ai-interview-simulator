# services/question_intelligence/question_set_builder.py

from typing import List

from domain.contracts.question.question import Question
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator
from services.question_intelligence.question_set_deduplicator import (
    QuestionSetDeduplicator,
)

from services.question_intelligence.area_question_builder import (
    AreaQuestionBuilder,
)

from services.question_intelligence.quality.question_set_quality_analyzer import (
    QuestionSetQualityAnalyzer,
)

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

from services.question_intelligence.interview_area_difficulty_profile import (
    order_areas_by_derived_difficulty,
)
from services.question_intelligence.interview_difficulty_ordering import (
    append_difficulty_to_memory_history,
    calculate_progression_score,
    order_questions_for_interview_progression,
)
from services.question_intelligence.interview_coherence_metrics import (
    InterviewCoherenceMetrics,
)
from services.question_intelligence.interview_theme_memory import (
    with_interview_theme_anchor,
)
from services.question_intelligence.interview_theme_selector import (
    InterviewThemeSelector,
)

from app.settings.constants import QUESTIONS_PER_AREA

from app.core.logger import get_logger

logger = get_logger(__name__)


class QuestionSetBuilder:
    """
    Facade that orchestrates per-area question generation, deduplication,
    ordering, and quality validation.

    Collaborators injected via constructor:
    - AreaQuestionBuilder       — per-area generation
    - QuestionSetDeduplicator   — exact + semantic deduplication
    - QuestionSetQualityAnalyzer — post-assembly quality report
    - InterviewThemeSelector    — theme anchor selection
    - InterviewCoherenceMetrics — coherence scoring
    """

    def __init__(
        self,
        area_builder: AreaQuestionBuilder,
        deduplicator: SemanticDeduplicator,
        quality_analyzer: QuestionSetQualityAnalyzer,
        theme_selector: InterviewThemeSelector | None = None,
        coherence_metrics: InterviewCoherenceMetrics | None = None,
    ) -> None:
        self._area_builder = area_builder
        self._set_deduplicator = QuestionSetDeduplicator(deduplicator)
        self._quality_analyzer = quality_analyzer
        self._theme_selector = (
            theme_selector if theme_selector is not None else InterviewThemeSelector()
        )
        self._coherence_metrics = (
            coherence_metrics
            if coherence_metrics is not None
            else InterviewCoherenceMetrics()
        )

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

        retrieval_memory = InterviewRetrievalMemory()

        # -----------------------------------------------------
        # THEME ANCHOR
        # -----------------------------------------------------

        ordered_areas = order_areas_by_derived_difficulty(areas)
        first_area = ordered_areas[0]
        theme_anchor = self._theme_selector.select_anchor(
            role=role,
            level=level,
            first_area=first_area,
        )
        retrieval_memory = with_interview_theme_anchor(
            retrieval_memory,
            theme_anchor,
        )

        logger.info("[QuestionSetBuilder] Theme anchor selected: %s", theme_anchor)

        # -----------------------------------------------------
        # INITIAL GENERATION
        # -----------------------------------------------------

        for area in ordered_areas:

            area_questions, retrieval_memory = self._area_builder.build(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
                questions_per_area=questions_per_area,
                memory=retrieval_memory,
            )

            if len(area_questions) < questions_per_area:
                logger.warning(
                    "[QuestionSetBuilder] Area %s produced %d questions (expected %d)",
                    area.value,
                    len(area_questions),
                    questions_per_area,
                )

            selected = area_questions[:questions_per_area]
            all_questions.extend(selected)

            for question in selected:
                retrieval_memory = retrieval_memory.model_copy(
                    update={
                        "difficulty_history": append_difficulty_to_memory_history(
                            retrieval_memory.difficulty_history,
                            question,
                        ),
                    }
                )

        # -----------------------------------------------------
        # DEDUP (INITIAL)
        # -----------------------------------------------------

        all_questions = self._set_deduplicator.deduplicate(all_questions)

        # -----------------------------------------------------
        # REFILL LOOP
        # -----------------------------------------------------

        max_attempts = 3
        attempt = 0
        refill_areas = self._set_deduplicator.refill_area_order(areas)

        while len(all_questions) < expected_total and attempt < max_attempts:

            missing = expected_total - len(all_questions)

            logger.info(
                "[QuestionSetBuilder] Refill attempt %d → missing %d",
                attempt + 1,
                missing,
            )

            for area in refill_areas:

                if missing <= 0:
                    break

                area_count = sum(1 for q in all_questions if q.area == area)

                if area_count >= questions_per_area:
                    continue

                new_questions, retrieval_memory = self._area_builder.build(
                    role=role,
                    level=level,
                    interview_type=interview_type,
                    area=area,
                    questions_per_area=1,
                    memory=retrieval_memory,
                )

                all_questions.extend(new_questions)
                missing -= len(new_questions)

            all_questions = self._set_deduplicator.deduplicate(all_questions)

            attempt += 1

        # -----------------------------------------------------
        # FINAL GUARD
        # -----------------------------------------------------

        if len(all_questions) < expected_total:
            logger.warning(
                "[QuestionSetBuilder] Could not reach expected size %d, got %d",
                expected_total,
                len(all_questions),
            )

        all_questions = all_questions[:expected_total]

        all_questions = order_questions_for_interview_progression(all_questions)

        # -----------------------------------------------------
        # FINAL VALIDATION
        # -----------------------------------------------------

        self._set_deduplicator.validate_no_duplicates(all_questions)

        quality_report = self._quality_analyzer.analyze(all_questions)
        progression_score = calculate_progression_score(all_questions)
        coherence = self._coherence_metrics.compute(
            questions=all_questions,
            memory=retrieval_memory,
        )

        logger.info(
            "[QUALITY] avg_similarity=%.2f max_similarity=%.2f duplicates=%s "
            "diversity=%.2f area_coverage=%.2f difficulty_balance=%.2f "
            "difficulty_progression_score=%.2f coherence_score=%s "
            "theme_anchor=%s theme_consistency=%s domain_continuity=%s",
            quality_report.similarity.average_similarity,
            quality_report.similarity.max_similarity,
            quality_report.similarity.duplicate_pairs,
            quality_report.diversity.diversity_score,
            quality_report.coverage.area_coverage_score,
            quality_report.coverage.difficulty_balance_score,
            progression_score,
            coherence["coherence_score"],
            coherence["theme_anchor"],
            coherence["theme_consistency"],
            coherence["domain_continuity"],
        )

        return all_questions
