# app/ui/dto/dimension_score_dto.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class DimensionScoreDTO:
    name: str
    score: Optional[float]
    max_score: float
    weight: float
    contribution: float
    is_evaluated: bool
