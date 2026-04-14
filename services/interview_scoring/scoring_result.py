# services/interview_scoring/scoring_result.py

from dataclasses import dataclass
from typing import Dict, Optional

from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType


@dataclass
class ScoringResult:
    dimension_scores: Dict[PerformanceDimensionType, Optional[float]]
    weighted_breakdown: Dict[PerformanceDimensionType, float]

    overall_score: float

    level: InterviewLevel
    hire_decision: HireDecision

    gating_triggered: bool
    gating_reason: Optional[str]

    hiring_probability: float
    percentile: float
    confidence: float
