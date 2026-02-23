# domain/contracts/interview_state.py

# Interview state contract
#
# This contract defines the structure of an interview state that can be used in the interview simulator.
# It is used to store the interview state in the database and to retrieve it when needed.
#
# The interview state is associated with an interview and contains the interview state.
# The interview state also contains the questions, answers, evaluations, and confidence.
# It must be:
# - complete when called standalone
# - no optional critical fields
# - respect field ownership
#
# A node can work with this object only, without the need of creating critical fields.

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.evaluation import EvaluationResult
from domain.contracts.confidence import Confidence


class InterviewState(BaseModel):

    # minimal setup already validated in Phase 1
    interview_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    language: str = Field(default="en")

    # progress tracking
    questions: list[Question] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
    evaluations: list[EvaluationResult] = Field(default_factory=list)

    # pointer to the current question
    current_question_id: Optional[str] = None

    # governance follow-up
    follow_up_count: int = Field(default=0, ge=0, le=2)

    # execution engines
    execution_results: list[str] = Field(default_factory=list)

    # aggregated scoring
    total_score: float = Field(default=0.0, ge=0.0, le=100.0)

    confidence: Optional[Confidence] = None

    # machine state
    completed: bool = False

    model_config = {"arbitrary_types_allowed": False}
