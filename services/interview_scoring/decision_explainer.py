# services/interview_scoring/decision_explainer.py

from typing import List, Dict, Optional

from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType


class DecisionExplainer:

    def explain(
        self,
        *,
        overall_score: float,
        _hire_decision: str,
        dimension_scores: Dict[PerformanceDimensionType, Optional[float]],
        gating_triggered: bool,
        gating_reason: str | None,
    ) -> List[str]:

        reasons: List[str] = []

        # -----------------------------------------------------
        # GATING
        # -----------------------------------------------------

        if gating_triggered:
            reasons.append(f"Gating rule triggered: {gating_reason}")
            return reasons

        # -----------------------------------------------------
        # OVERALL SCORE
        # -----------------------------------------------------

        if overall_score < 60:
            reasons.append("Overall score is below the expected hiring threshold (60).")

        if overall_score >= 70:
            reasons.append("Candidate demonstrates strong overall performance.")
        
        if overall_score >= 80:
            reasons.append("Candidate demonstrates exceptional overall performance.")

        # -----------------------------------------------------
        # WEAK DIMENSIONS
        # -----------------------------------------------------

        weak_dims = [
            dim for dim, score in dimension_scores.items() if score < 40 and score > 0
        ]

        for dim in weak_dims:
            label = DIMENSION_LABELS.get(dim, dim.value)
            reasons.append(
                f"{label} is below acceptable level ({dimension_scores[dim]:.1f})."
            )

        # -----------------------------------------------------
        # STRONG DIMENSIONS
        # -----------------------------------------------------

        strong_dims = [
            dim
            for dim, score in dimension_scores.items()
            if score >= 80 and score < 100
        ]

        if strong_dims and weak_dims:
            reasons.append(
                "Performance is unbalanced: strong areas do not compensate critical weaknesses."
            )

        # -----------------------------------------------------
        # FALLBACK
        # -----------------------------------------------------

        if not reasons:
            reasons.append("Candidate meets overall expectations.")

        return reasons
