# services/planning/contracts/planner_score_breakdown.py

from pydantic import BaseModel


class PlannerScoreBreakdown(BaseModel):

    difficulty_score: float

    cluster_penalty: float

    novelty_bonus: float

    category_rarity_bonus: float

    final_score: float

    rationale: list[str]

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
