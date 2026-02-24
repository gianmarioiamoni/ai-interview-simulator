# domain/contracts/question_evaluation.py

# Question-level evaluation contract
#
# Represents the evaluation of a single written answer.
# Produced by the evaluator node during the interview flow.
#
# Responsibility: immutable per-question evaluation result.

from pydantic import BaseModel, Field


class QuestionEvaluation(BaseModel):
    question_id: str = Field(..., min_length=1)

    score: float = Field(..., ge=0.0, le=100.0)
    max_score: float = Field(..., gt=0.0)

    feedback: str = Field(..., min_length=1)

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    passed: bool

    model_config = {"frozen": True}
