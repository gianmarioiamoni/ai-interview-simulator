# domain/contracts/question_evaluation.py


from pydantic import BaseModel, Field
from typing import Optional


class QuestionEvaluation(BaseModel):
    question_id: str = Field(..., min_length=1)

    score: float = Field(..., ge=0.0, le=100.0)
    max_score: float = Field(..., gt=0.0)

    feedback: str = Field(..., min_length=1)

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    passed: bool

    # execution metadata
    passed_tests: Optional[int] = None
    total_tests: Optional[int] = None
    execution_status: Optional[str] = None

    model_config = {"frozen": True}

    tokens_used: int = 0
