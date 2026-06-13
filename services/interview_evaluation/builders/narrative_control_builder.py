# services/interview_evaluation/builders/narrative_control_builder.py

from typing import List, Dict
from infrastructure.config.evaluation import (
    NARRATIVE_BALANCE_BALANCED_SPREAD,
    NARRATIVE_BALANCE_SLIGHTLY_UNEVEN_SPREAD,
    NARRATIVE_EXCELLENT_THRESHOLD,
    NARRATIVE_STRONG_THRESHOLD,
    NARRATIVE_MODERATE_THRESHOLD,
)


class NarrativeControlBuilder:

    def build_summary_payload(
        self,
        decision: str,
        overall_score: float,
        percentile: float,
        dimensions: List[Dict],
    ) -> Dict:

        if not dimensions:
            return {
                "decision": decision,
                "overall_score": overall_score,
                "percentile": percentile,
                "strongest": "N/A",
                "strongest_score": 0,
                "weakest": "N/A",
                "weakest_score": 0,
                "balance_flag": "BALANCED",
                "classification": {},
            }

        strongest = max(dimensions, key=lambda x: x["score"])
        weakest = min(dimensions, key=lambda x: x["score"])

        spread = strongest["score"] - weakest["score"]

        if spread < NARRATIVE_BALANCE_BALANCED_SPREAD:
            balance_flag = "BALANCED"
        elif spread < NARRATIVE_BALANCE_SLIGHTLY_UNEVEN_SPREAD:
            balance_flag = "SLIGHTLY_UNEVEN"
        else:
            balance_flag = "UNBALANCED"

        def classify(score: float) -> str:
            if score >= NARRATIVE_EXCELLENT_THRESHOLD:
                return "excellent"
            elif score >= NARRATIVE_STRONG_THRESHOLD:
                return "strong"
            elif score >= NARRATIVE_MODERATE_THRESHOLD:
                return "moderate"
            else:
                return "weak"

        return {
            "decision": decision,
            "overall_score": overall_score,
            "percentile": percentile,
            "strongest": strongest["name"],
            "strongest_score": strongest["score"],
            "weakest": weakest["name"],
            "weakest_score": weakest["score"],
            "balance_flag": balance_flag,
            "classification": {d["name"]: classify(d["score"]) for d in dimensions},
        }
