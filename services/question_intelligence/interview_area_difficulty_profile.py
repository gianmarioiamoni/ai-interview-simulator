# services/question_intelligence/interview_area_difficulty_profile.py

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from statistics import mean

from domain.contracts.interview.interview_area import InterviewArea

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CORPUS_ROOTS = (
    _PROJECT_ROOT / "datasets/curated/hf_import",
    _PROJECT_ROOT / "datasets/curated/interview_seed",
    _PROJECT_ROOT / "datasets/curated/local_import",
    _PROJECT_ROOT / "datasets/curated",
)


@lru_cache(maxsize=1)
def compute_area_average_difficulties() -> dict[str, float]:

    totals: dict[str, list[int]] = {}

    for root in _CORPUS_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.json"):
            try:
                payload = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(payload, list):
                continue

            for item in payload:
                if not isinstance(item, dict):
                    continue

                area = item.get("area")
                difficulty = item.get("difficulty")

                if not area or difficulty is None:
                    continue

                try:
                    difficulty_int = int(difficulty)
                except (TypeError, ValueError):
                    continue

                totals.setdefault(str(area), []).append(difficulty_int)

    return {
        area: round(mean(values), 4)
        for area, values in totals.items()
        if values
    }


def order_areas_by_derived_difficulty(
    areas: list[InterviewArea],
) -> list[InterviewArea]:

    averages = compute_area_average_difficulties()

    return sorted(
        areas,
        key=lambda area: averages.get(area.value, 3.0),
    )
