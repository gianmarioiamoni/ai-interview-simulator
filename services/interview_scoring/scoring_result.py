# services/interview_scoring/scoring_result.py

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ScoringResult:
    dimension_scores: Dict[str, float]
    weighted_breakdown: Dict[str, float]
    overall_score: float
    gating_triggered: bool
    gating_reason: Optional[str]
    hiring_probability: float
    percentile: float
    confidence: float
