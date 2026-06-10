# tests/services/test_question_set_builder.py

from types import SimpleNamespace
from unittest.mock import MagicMock

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import (
    Question,
    QuestionDifficulty,
    QuestionType,
)
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_intelligence.question_set_builder import QuestionSetBuilder


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

AREAS = [
    InterviewArea.TECH_BACKGROUND,
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
]


def build_question(area: InterviewArea, idx: int, prompt: str | None = None) -> Question:
    return Question(
        id=f"{area.value}-{idx}",
        area=area,
        type=QuestionType.WRITTEN,
        prompt=prompt or f"{area.value} question {idx}",
        difficulty=QuestionDifficulty.MEDIUM,
    )


class StubAreaBuilder:
    """Returns pre-configured questions per (area, call) and echoes memory."""

    def __init__(self, responses: dict[InterviewArea, list[list[Question]]]):
        self._responses = responses
        self.calls: list[InterviewArea] = []

    def build(self, *, role, level, interview_type, area, questions_per_area, memory):
        self.calls.append(area)

        queue = self._responses.get(area, [])
        questions = queue.pop(0) if queue else []

        return questions, memory


def build_quality_report() -> SimpleNamespace:
    return SimpleNamespace(
        similarity=SimpleNamespace(
            average_similarity=0.1,
            max_similarity=0.2,
            duplicate_pairs=0,
        ),
        diversity=SimpleNamespace(diversity_score=0.9),
        coverage=SimpleNamespace(
            area_coverage_score=1.0,
            difficulty_balance_score=0.8,
        ),
    )


def build_set_builder(area_builder: StubAreaBuilder) -> QuestionSetBuilder:

    deduplicator = MagicMock()
    deduplicator.deduplicate.side_effect = lambda questions: questions

    quality_analyzer = MagicMock()
    quality_analyzer.analyze.return_value = build_quality_report()

    theme_selector = MagicMock()
    theme_selector.select_anchor.return_value = "api_design"

    coherence_metrics = MagicMock()
    coherence_metrics.compute.return_value = {
        "coherence_score": 0.9,
        "theme_anchor": "api_design",
        "theme_consistency": 0.9,
        "domain_continuity": 0.8,
    }

    return QuestionSetBuilder(
        area_builder=area_builder,
        deduplicator=deduplicator,
        quality_analyzer=quality_analyzer,
        theme_selector=theme_selector,
        coherence_metrics=coherence_metrics,
    )


def run_build(builder: QuestionSetBuilder, questions_per_area: int):
    return builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        areas=AREAS,
        questions_per_area=questions_per_area,
    )


# ---------------------------------------------------------
# TESTS
# ---------------------------------------------------------


def test_build_returns_expected_total_questions():

    area_builder = StubAreaBuilder(
        {
            area: [[build_question(area, i) for i in range(2)]]
            for area in AREAS
        }
    )

    builder = build_set_builder(area_builder)

    result = run_build(builder, questions_per_area=2)

    assert len(result) == 4
    assert {q.area for q in result} == set(AREAS)


def test_build_trims_area_overflow():

    # each area produces 4 questions but only 2 are requested
    area_builder = StubAreaBuilder(
        {
            area: [[build_question(area, i) for i in range(4)]]
            for area in AREAS
        }
    )

    builder = build_set_builder(area_builder)

    result = run_build(builder, questions_per_area=2)

    assert len(result) == 4

    for area in AREAS:
        assert sum(1 for q in result if q.area == area) == 2


def test_build_removes_exact_duplicates_and_refills():

    area = AREAS[0]
    other = AREAS[1]

    duplicated = [
        build_question(area, 1, prompt="Same prompt"),
        build_question(area, 2, prompt="Same prompt"),
    ]

    refill = [build_question(area, 3, prompt="Fresh prompt")]

    area_builder = StubAreaBuilder(
        {
            area: [duplicated, refill],
            other: [[build_question(other, i) for i in range(2)]],
        }
    )

    builder = build_set_builder(area_builder)

    result = run_build(builder, questions_per_area=2)

    prompts = [q.prompt.strip().lower() for q in result]

    assert len(prompts) == len(set(prompts))
    assert len(result) == 4
    assert area_builder.calls.count(area) >= 2  # refill attempted


def test_build_returns_partial_set_when_refill_exhausted():

    area = AREAS[0]
    other = AREAS[1]

    area_builder = StubAreaBuilder(
        {
            area: [[build_question(area, 1)]],  # only 1 instead of 2, no refill
            other: [[build_question(other, i) for i in range(2)]],
        }
    )

    builder = build_set_builder(area_builder)

    result = run_build(builder, questions_per_area=2)

    assert len(result) == 3
