# domain/contracts/question.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

from domain.contracts.interview_area import InterviewArea
from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.coding_spec import CodingSpec


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

    # LEGACY (deprecabile dopo FASE 2)
    function_name: str = "solution"

    # NEW
    coding_spec: Optional[CodingSpec] = None

    # =========================================================
    # TYPE HELPERS
    # =========================================================

    def is_coding(self) -> bool:
        return self.type == QuestionType.CODING

    def is_written(self) -> bool:
        return self.type == QuestionType.WRITTEN

    def is_database(self) -> bool:
        return self.type == QuestionType.DATABASE

    def is_execution_based(self) -> bool:
        return self.type in (QuestionType.CODING, QuestionType.DATABASE)

    # =========================================================

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
