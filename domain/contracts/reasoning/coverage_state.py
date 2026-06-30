# domain/contracts/reasoning/coverage_state.py

from pydantic import BaseModel, Field


class CoverageState(BaseModel):
    """Interview area coverage accumulated during the session.

    Tracks which areas have been visited, how deeply, which questions
    triggered follow-ups, and which topics recurred.
    Single-writer: InterviewReasoner (ADR-038).
    """

    covered_areas: list[str] = Field(default_factory=list)
    # area -> number of questions asked in that area
    coverage_depth: dict[str, int] = Field(default_factory=dict)
    # question_ids that triggered a follow-up
    follow_up_history: list[str] = Field(default_factory=list)
    # topics observed more than once across the session
    repeated_topics: list[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}
