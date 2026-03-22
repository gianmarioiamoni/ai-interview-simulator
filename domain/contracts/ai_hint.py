# domain/contracts/ai_hint.py

from pydantic import BaseModel
from typing import List, Optional

from domain.contracts.hint_level import HintLevel


class AIHintInput(BaseModel):
    error: Optional[str] = None
    user_code: str
    failed_tests: List[dict] = [] 
    question: str
    hint_level: HintLevel = HintLevel.BASIC


class AIHint(BaseModel):
    explanation: str
    suggestion: str

    model_config = {"frozen": True}
