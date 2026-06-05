# tests/services/question_intelligence/test_question_set_difficulty_progression.py

from unittest.mock import MagicMock

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.interview_area_difficulty_profile import (
    compute_area_average_difficulties,
    order_areas_by_derived_difficulty,
)
from services.question_intelligence.interview_difficulty_ordering import (
    append_difficulty_to_memory_history,
    calculate_progression_score,
    order_questions_for_interview_progression,
)
from services.question_intelligence.question_difficulty_mapper import (
    question_difficulty_to_corpus_int,
)
from services.question_intelligence.question_set_builder import QuestionSetBuilder
from services.question_intelligence.quality.question_set_quality_analyzer import (
    QuestionSetQualityAnalyzer,
)
from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator


def _written_question(
    area: InterviewArea,
    difficulty: QuestionDifficulty,
    question_id: str,
) -> Question:

    return Question(
        id=question_id,
        area=area,
        type=QuestionType.WRITTEN,
        prompt=f"Prompt for {area.value} {question_id}",
        difficulty=difficulty,
    )


def test_compute_area_average_difficulties_from_corpus() -> None:

    averages = compute_area_average_difficulties()

    assert averages
    assert "technical_background" in averages
    assert "technical_coding" in averages


def test_order_areas_by_derived_difficulty_is_monotonic() -> None:

    areas = InterviewType.TECHNICAL.get_areas()
    averages = compute_area_average_difficulties()
    ordered = order_areas_by_derived_difficulty(areas)

    difficulties = [averages.get(area.value, 3.0) for area in ordered]

    assert difficulties == sorted(difficulties)


def test_append_difficulty_to_memory_history() -> None:

    question = _written_question(
        InterviewArea.TECH_BACKGROUND,
        QuestionDifficulty.EASY,
        "q-1",
    )

    updated = append_difficulty_to_memory_history([], question)

    assert updated == [question_difficulty_to_corpus_int(QuestionDifficulty.EASY)]


def test_order_questions_for_interview_progression_is_monotonic() -> None:

    questions = [
        _written_question(InterviewArea.TECH_CODING, QuestionDifficulty.HARD, "c"),
        _written_question(InterviewArea.TECH_BACKGROUND, QuestionDifficulty.EASY, "b"),
        _written_question(
            InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            QuestionDifficulty.MEDIUM,
            "k",
        ),
    ]

    ordered = order_questions_for_interview_progression(questions)
    levels = [question_difficulty_to_corpus_int(q.difficulty) for q in ordered]

    assert levels == sorted(levels)
    assert {q.area for q in ordered} == {q.area for q in questions}
    assert len(ordered) == len(questions)


def test_calculate_progression_score_perfect_for_monotonic_set() -> None:

    questions = [
        _written_question(InterviewArea.TECH_BACKGROUND, QuestionDifficulty.EASY, "1"),
        _written_question(
            InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            QuestionDifficulty.MEDIUM,
            "2",
        ),
        _written_question(InterviewArea.TECH_CODING, QuestionDifficulty.HARD, "3"),
    ]

    assert calculate_progression_score(questions) == 1.0


def test_question_set_builder_updates_difficulty_history_per_area() -> None:

    areas = [
        InterviewArea.TECH_BACKGROUND,
        InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    ]

    area_builder = MagicMock()

    area_builder.build.side_effect = lambda **kwargs: (
        [
            _written_question(
                kwargs["area"],
                QuestionDifficulty.EASY,
                f"id-{kwargs['area'].value}",
            ),
        ],
        kwargs.get("memory") or InterviewRetrievalMemory(),
    )

    deduplicator = MagicMock()
    deduplicator.deduplicate.side_effect = lambda questions: questions

    builder = QuestionSetBuilder(
        area_builder=area_builder,
        deduplicator=deduplicator,
        quality_analyzer=QuestionSetQualityAnalyzer(),
    )

    builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        areas=areas,
        questions_per_area=1,
    )

    second_call_memory = area_builder.build.call_args_list[1].kwargs["memory"]
    assert len(second_call_memory.difficulty_history) >= 1


def test_question_set_builder_preserves_area_coverage_and_count() -> None:

    areas = InterviewType.TECHNICAL.get_areas()
    area_builder = MagicMock()

    area_builder.build.side_effect = lambda **kwargs: (
        [
            _written_question(
                kwargs["area"],
                QuestionDifficulty.MEDIUM,
                f"id-{kwargs['area'].value}",
            ),
        ],
        kwargs.get("memory") or InterviewRetrievalMemory(),
    )

    deduplicator = MagicMock()
    deduplicator.deduplicate.side_effect = lambda questions: questions

    builder = QuestionSetBuilder(
        area_builder=area_builder,
        deduplicator=deduplicator,
        quality_analyzer=QuestionSetQualityAnalyzer(),
    )

    result = builder.build(
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        areas=areas,
        questions_per_area=1,
    )

    assert len(result) == len(areas)
    assert {q.area for q in result} == set(areas)
