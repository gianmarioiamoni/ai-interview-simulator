# services/planning/contracts/planner_telemetry.py

from pydantic import BaseModel


class PlannerTelemetry(BaseModel):

    total_candidates: int

    selected_candidates: int

    rejected_candidates: int

    average_selection_score: float

    average_difficulty: float

    semantic_penalty_count: int

    novelty_bonus_count: int

    rarity_bonus_count: int

    unique_areas: int

    area_distribution: dict[str, int]

    rationale_distribution: dict[str, int]

    difficulty_spike_penalty_count: int

    difficulty_progression_score: float

    embedding_model: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

