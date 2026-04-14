# services/interview_scoring/decision_explainer.py

from typing import List, Dict

from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS


class DecisionExplainer:

    def explain(
        self,
        *,
        overall_score: float,
        hire_decision: str,
        dimension_scores: Dict[str, float],
        gating_triggered: bool,
        gating_reason: str | None,
    ) -> List[str]:

        reasons: List[str] = []

        # -----------------------------------------------------
        # GATING (highest priority)
        # -----------------------------------------------------

        if gating_triggered:
            reasons.append(f"Gating rule triggered: {gating_reason}")
            return reasons

        # -----------------------------------------------------
        # OVERALL SCORE
        # -----------------------------------------------------

        if overall_score < 60:
            reasons.append("Overall score is below the expected hiring threshold (60).")

        # -----------------------------------------------------
        # WEAK DIMENSIONS
        # -----------------------------------------------------

        weak_dims = [
            k for k, v in dimension_scores.items()
             if v < 40 and v > 0]

        for dim in weak_dims:
            reasons.append(
                f"{DIMENSION_LABELS[dim]} is below acceptable level ({dimension_scores[dim]:.1f})."
            )

        # -----------------------------------------------------
        # STRONG DIMENSIONS (for balance reasoning)
        # -----------------------------------------------------

        strong_dims = [
            k for k, v in dimension_scores.items()
            if v >= 80 and v < 100
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
