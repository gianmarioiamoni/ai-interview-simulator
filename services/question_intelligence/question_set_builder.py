# services/question_intelligence/question_set_builder.py

from typing import List

from domain.contracts.question.question import Question
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator

from services.question_intelligence.question_set_coding_dedup import (
    prioritize_corpus_coding_for_dedup,
)
from services.question_intelligence.question_set_knowledge_dedup import (
    prioritize_technical_knowledge_for_dedup,
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
    def __init__(
        self,
        area_builder: AreaQuestionBuilder,
        deduplicator: SemanticDeduplicator,
        quality_analyzer: QuestionSetQualityAnalyzer,
        theme_selector: InterviewThemeSelector | None = None,
        coherence_metrics: InterviewCoherenceMetrics | None = None,
    ) -> None:
        self._area_builder = area_builder
        self._deduplicator = deduplicator
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

        logger.info(
            f"[QuestionSetBuilder] Theme anchor selected: {theme_anchor}",
        )

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
                    f"[QuestionSetBuilder] Area {area.value} produced "
                    f"{len(area_questions)} questions (expected {questions_per_area})"
                )

            selected = area_questions[:questions_per_area]
            all_questions.extend(selected)

            for question in selected:
                retrieval_memory = InterviewRetrievalMemory(
                    asked_question_ids=retrieval_memory.asked_question_ids,
                    covered_domains=retrieval_memory.covered_domains,
                    weak_domains=retrieval_memory.weak_domains,
                    strong_domains=retrieval_memory.strong_domains,
                    difficulty_history=append_difficulty_to_memory_history(
                        retrieval_memory.difficulty_history,
                        question,
                    ),
                    average_score=retrieval_memory.average_score,
                    question_count=retrieval_memory.question_count,
                )

        # -----------------------------------------------------
        # DEDUP (INITIAL)
        # -----------------------------------------------------

        all_questions = self._deduplicate_for_set(all_questions)

        # -----------------------------------------------------
        # REFILL LOOP (STEP 2.4)
        # -----------------------------------------------------

        max_attempts = 3
        attempt = 0
        refill_areas = self._refill_area_order(areas)

        while len(all_questions) < expected_total and attempt < max_attempts:

            missing = expected_total - len(all_questions)

            logger.info(
                f"[QuestionSetBuilder] Refill attempt {attempt+1} → missing {missing}"
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

            all_questions = self._deduplicate_for_set(all_questions)

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

        all_questions = order_questions_for_interview_progression(all_questions)

        # -----------------------------------------------------
        # FINAL VALIDATION
        # -----------------------------------------------------

        self._validate_no_duplicates(all_questions)

        quality_report = self._quality_analyzer.analyze(all_questions)
        progression_score = calculate_progression_score(all_questions)
        coherence = self._coherence_metrics.compute(
            questions=all_questions,
            memory=retrieval_memory,
        )

        logger.info(
            f"[QUALITY] "
            f"avg_similarity={quality_report.similarity.average_similarity:.2f} "
            f"max_similarity={quality_report.similarity.max_similarity:.2f} "
            f"duplicates={quality_report.similarity.duplicate_pairs} "
            f"diversity={quality_report.diversity.diversity_score:.2f} "
            f"area_coverage={quality_report.coverage.area_coverage_score:.2f} "
            f"difficulty_balance={quality_report.coverage.difficulty_balance_score:.2f} "
            f"difficulty_progression_score={progression_score:.2f} "
            f"coherence_score={coherence['coherence_score']} "
            f"theme_anchor={coherence['theme_anchor']} "
            f"theme_consistency={coherence['theme_consistency']} "
            f"domain_continuity={coherence['domain_continuity']}"
        )

        return all_questions

    # =========================================================
    # HELPERS
    # =========================================================

    def _deduplicate_for_set(self, questions: List[Question]) -> List[Question]:

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
                area_questions = prioritize_technical_knowledge_for_dedup(
                    area_questions,
                )
            elif area == InterviewArea.TECH_CODING:
                area_questions = prioritize_corpus_coding_for_dedup(area_questions)

            deduped.extend(self._deduplicator.deduplicate(area_questions))

        return deduped

    def _refill_area_order(self, areas: List[InterviewArea]) -> List[InterviewArea]:

        knowledge = InterviewArea.TECH_TECHNICAL_KNOWLEDGE
        prioritized = [a for a in areas if a == knowledge]
        prioritized.extend(a for a in areas if a != knowledge)
        return prioritized

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
