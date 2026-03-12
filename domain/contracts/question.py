# domain/contracts/question.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

from domain.contracts.interview_area import InterviewArea
from domain.contracts.test_case import TestCase


class QuestionType(str, Enum):
    WRITTEN = "written"
    CODING = "coding"
    DATABASE = "database"


class Question(BaseModel):
    id: str = Field(..., min_length=1)
    area: InterviewArea
    type: QuestionType
    prompt: str = Field(..., min_length=1)
    reference_solution: Optional[str] = None
    difficulty: int = Field(..., ge=1, le=5)
    humanized: bool = False
    test_cases: list[TestCase] = Field(default_factory=list)
    visible_tests: list[TestCase] = Field(default_factory=list)
    hidden_tests: list[TestCase] = Field(default_factory=list)
    db_schema: Optional[str] = None
    db_seed_data: Optional[str] = None

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
