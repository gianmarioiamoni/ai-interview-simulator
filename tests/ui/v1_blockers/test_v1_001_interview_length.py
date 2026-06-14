# tests/ui/v1_blockers/test_v1_001_interview_length.py

import pytest

from domain.contracts.interview.interview_type import InterviewType
from app.settings.constants import (
    DEFAULT_INTERVIEW_LENGTH,
    TECHNICAL_AREA_WEIGHTS,
)
from services.interview_length.interview_length_planner import (
    compute_questions_per_area as _compute_questions_per_area,
    expand_planned_areas as _expand_planned_areas,
)


TECHNICAL_AREAS = InterviewType.TECHNICAL.get_areas()
HR_AREAS = InterviewType.HR.get_areas()


class TestDefaultInterviewLength:
    def test_default_is_20(self):
        assert DEFAULT_INTERVIEW_LENGTH == 20


class TestComputeQuestionsPerArea:
    def test_technical_20q_sum_equals_20(self):
        counts = _compute_questions_per_area(
            interview_length=20,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        assert sum(counts.values()) == 20

    def test_technical_10q_sum_equals_10(self):
        counts = _compute_questions_per_area(
            interview_length=10,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        assert sum(counts.values()) == 10

    def test_technical_30q_sum_equals_30(self):
        counts = _compute_questions_per_area(
            interview_length=30,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        assert sum(counts.values()) == 30

    def test_all_areas_get_at_least_one_question(self):
        for length in [10, 20, 30]:
            counts = _compute_questions_per_area(
                interview_length=length,
                areas=TECHNICAL_AREAS,
                weights=TECHNICAL_AREA_WEIGHTS,
            )
            for area in TECHNICAL_AREAS:
                assert counts[area.value] >= 1, f"Area {area.value} has 0 questions for length {length}"

    def test_hr_no_weights_distributes_evenly(self):
        counts = _compute_questions_per_area(
            interview_length=10,
            areas=HR_AREAS,
            weights=None,
        )
        assert sum(counts.values()) == 10

    def test_empty_areas_returns_empty_dict(self):
        result = _compute_questions_per_area(interview_length=20, areas=[], weights=None)
        assert result == {}


class TestExpandPlannedAreas:
    def test_expand_produces_correct_total_for_20q(self):
        counts = _compute_questions_per_area(
            interview_length=20,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        planned = _expand_planned_areas(counts, TECHNICAL_AREAS)
        assert len(planned) == 20

    def test_expand_produces_correct_total_for_10q(self):
        counts = _compute_questions_per_area(
            interview_length=10,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        planned = _expand_planned_areas(counts, TECHNICAL_AREAS)
        assert len(planned) == 10

    def test_expand_produces_correct_total_for_30q(self):
        counts = _compute_questions_per_area(
            interview_length=30,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        planned = _expand_planned_areas(counts, TECHNICAL_AREAS)
        assert len(planned) == 30

    def test_expand_contains_all_area_values(self):
        counts = _compute_questions_per_area(
            interview_length=20,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        planned = _expand_planned_areas(counts, TECHNICAL_AREAS)
        for area in TECHNICAL_AREAS:
            assert area.value in planned

    def test_expand_area_repetitions_match_counts(self):
        counts = _compute_questions_per_area(
            interview_length=20,
            areas=TECHNICAL_AREAS,
            weights=TECHNICAL_AREA_WEIGHTS,
        )
        planned = _expand_planned_areas(counts, TECHNICAL_AREAS)
        for area_value, count in counts.items():
            assert planned.count(area_value) == count
