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

        if spread < 15:
            balance_flag = "BALANCED"
        elif spread < 25:
            balance_flag = "SLIGHTLY_UNEVEN"
        else:
            balance_flag = "UNBALANCED"

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
            "balance_flag": balance_flag,
            "classification": {d["name"]: classify(d["score"]) for d in dimensions},
        }
