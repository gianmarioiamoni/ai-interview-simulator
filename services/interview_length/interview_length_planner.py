# services/interview_length/interview_length_planner.py

import math
from domain.contracts.interview.interview_area import InterviewArea


def compute_questions_per_area(
    interview_length: int,
    areas: list[InterviewArea],
    weights: dict[str, float] | None = None,
) -> dict[str, int]:
    """Distribute `interview_length` questions across areas.

    When weights are provided (technical interview), each area receives a share
    proportional to its weight, with a minimum of 1.  Remainder questions are
    distributed to the areas with the largest fractional parts.

    When weights are absent (HR interview) questions are distributed evenly.
    """
    n_areas = len(areas)
    if n_areas == 0:
        return {}

    if weights:
        raw = {a.value: weights.get(a.value, 1.0 / n_areas) * interview_length for a in areas}
        counts: dict[str, int] = {k: max(1, math.floor(v)) for k, v in raw.items()}
        remainder = interview_length - sum(counts.values())
        if remainder > 0:
            fractions = sorted(
                [(a.value, raw[a.value] - math.floor(raw[a.value])) for a in areas],
                key=lambda x: -x[1],
            )
            for k, _ in fractions[:remainder]:
                counts[k] += 1
        return counts

    base = interview_length // n_areas
    extra = interview_length % n_areas
    return {a.value: base + (1 if i < extra else 0) for i, a in enumerate(areas)}


def expand_planned_areas(
    area_question_counts: dict[str, int],
    areas: list[InterviewArea],
) -> list[str]:
    """Build an ordered planned_areas list by repeating each area value according to its count.

    For a 20-question interview with counts
    {'technical_background': 2, 'technical_coding': 5, ...}
    this returns a list of 20 area value strings that AdaptiveNavigationNode
    iterates one-by-one.  Areas appear in the same order as the input `areas` list.
    """
    result: list[str] = []
    for area in areas:
        count = area_question_counts.get(area.value, 1)
        result.extend([area.value] * count)
    return result
