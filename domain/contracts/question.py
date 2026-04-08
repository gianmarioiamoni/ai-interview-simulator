# domain/contracts/question.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

from domain.contracts.interview_area import InterviewArea
from domain.contracts.coding_test_case import CodingTestCase
from domain.contracts.coding_spec import CodingSpec


class QuestionType(str, Enum):
    WRITTEN = "written"
    CODING = "coding"
    DATABASE = "database"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(BaseModel):
    id: str = Field(..., min_length=1)
    area: InterviewArea
    type: QuestionType
    prompt: str = Field(..., min_length=1)
    reference_solution: Optional[str] = None
    difficulty: QuestionDifficulty = Field(default=QuestionDifficulty.MEDIUM)
    humanized: bool = False
    visible_tests: list[CodingTestCase] = Field(default_factory=list)
    hidden_tests: list[CodingTestCase] = Field(default_factory=list)
    db_schema: Optional[str] = None
    db_seed_data: Optional[str] = None
    expected_rows: Optional[list[tuple]] = None
    expected_ordered: bool = Field(default=True)
    function_name: str = "solution"
    coding_spec: Optional[CodingSpec] = None

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
