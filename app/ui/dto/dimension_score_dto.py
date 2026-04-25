# app/ui/dto/dimension_score_dto.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class DimensionScoreDTO:
    name: str
    score: Optional[float]
  
