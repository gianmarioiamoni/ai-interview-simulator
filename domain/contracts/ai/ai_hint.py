# domain/contracts/ai_hint.py

from pydantic import BaseModel
from typing import Optional

from domain.contracts.ai.hint_level import HintLevel


class AIHintInput(BaseModel):
    error: Optional[str] = None
    user_code: str
    failed_tests: str
    question: str
    hint_level: HintLevel = HintLevel.BASIC


class AIHint(BaseModel):
    explanation: str
    suggestion: str

    model_config = {"frozen": True}
