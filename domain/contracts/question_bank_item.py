# app/domain/contracts/question_bank_item.py

# QuestionBankItem contract
#
# Represents a curated question stored in the semantic question bank.
# This is NOT the runtime interview question.
# It includes metadata required for RAG filtering and retrieval.

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class QuestionBankItem(BaseModel):
    id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)

    interview_type: Literal["hr", "technical"]
    role: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1)

    level: Literal["junior", "mid", "senior"]
    difficulty: int = Field(..., ge=1, le=5)

    model_config = {"frozen": True}
