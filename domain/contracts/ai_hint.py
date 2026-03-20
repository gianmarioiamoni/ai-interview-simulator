# domain/contracts/ai_hint.py

from pydantic import BaseModel
from typing import List, Optional


class AIHintInput(BaseModel):
    error: Optional[str] = None
    user_code: str
    failed_tests: List[dict] = []  # simple for now


class AIHint(BaseModel):
    explanation: str
    suggestion: str

    model_config = {"frozen": True}
