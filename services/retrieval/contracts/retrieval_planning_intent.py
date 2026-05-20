# services/retrieval/contracts/retrieval_planning_intent.py

from pydantic import BaseModel


class RetrievalPlanningIntent(BaseModel):

    focus_areas: list[str]

    required_tags: list[str]

    target_level: str

    query_text: str

    max_candidates: int = 15

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
