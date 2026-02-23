# domain/contracts/evaluation.py

# Evaluation contract
#
# This contract defines the structure of an evaluation result that can be used in the interview simulator.
# It is used to store the evaluation result in the database and to retrieve it when needed.
#
# The evaluation result is associated with a question and contains the evaluation result.
# The evaluation result also contains the score, the max score, the feedback, the strengths, the weaknesses, and whether the candidate passed the question.
#
# Responsability: represents a frozen and immutable evaluation result in time. 
# It is the output of evaluator LLM

from pydantic import BaseModel, Field
from typing import Optional


class EvaluationResult(BaseModel):
    question_id: str = Field(..., min_length=1)

    score: float = Field(..., ge=0.0, le=100.0)
    max_score: float = Field(..., gt=0.0)

    feedback: str = Field(..., min_length=1)

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    passed: bool

    model_config = {"frozen": True}
