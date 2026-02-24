# app/domain/contracts/question.py

# Question contract
#
# This contract defines the structure of a question that can be used in the interview simulator.
# It is used to store the question in the database and to retrieve it when needed.
#
# The question can be of type written, coding, or database.
# The written question is a simple text question.
# The coding question is a question that requires the candidate to write code to solve a problem.
# The database question is a question that requires the candidate to write SQL code to solve a problem.
#
# Responsability: represents a frozen and immutable question in time.
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    WRITTEN = "written"
    CODING = "coding"
    DATABASE = "database"


class Question(BaseModel):
    id: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1)
    type: QuestionType
    prompt: str = Field(..., min_length=1)

    # optional for coding/db
    reference_solution: Optional[str] = None

    # difficulty useful for future scoring
    difficulty: int = Field(..., ge=1, le=5)

    humanized: bool = False

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
