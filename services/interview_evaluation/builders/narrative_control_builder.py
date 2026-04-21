# services/interview_evaluation/builders/narrative_control_builder.py

from typing import List, Dict


class NarrativeControlBuilder:

    def build_summary_payload(
        self,
        decision: str,
        overall_score: float,
        percentile: float,
        dimensions: List[Dict],
    ) -> Dict:

        if not dimensions:
            return {}

        strongest = max(dimensions, key=lambda x: x["score"])
        weakest = min(dimensions, key=lambda x: x["score"])

        spread = strongest["score"] - weakest["score"]

        is_balanced = spread < 10

        # -----------------------------------------------------
        # semantic classification
        # -----------------------------------------------------

        def classify(score: float) -> str:
            if score >= 90:
                return "excellent"
            elif score >= 80:
                return "strong"
            elif score >= 70:
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
            "is_balanced": is_balanced,
            "spread": spread,
            "classification": {d["name"]: classify(d["score"]) for d in dimensions},
        }
