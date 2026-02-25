# app/ui/dto/dimension_score_dto.py

from dataclasses import dataclass


@dataclass
class DimensionScoreDTO:
    name: str
    score: float
    max_score: float
