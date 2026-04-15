# app/ui/services/report_insight_builder.py

from typing import List
from app.ui.dto.dimension_score_dto import DimensionScoreDTO


class DimensionInsight:

    def __init__(self, name: str, score: float, weight: float, impact: str):
        self.name = name
        self.score = score
        self.weight = weight
        self.impact = impact


class ReportInsightBuilder:

    # ---------------------------------------------------------
    # DIMENSION IMPACT
    # ---------------------------------------------------------

    def build_dimension_insights(
        self,
        dimensions: List[DimensionScoreDTO],
    ) -> List[DimensionInsight]:

        insights = []

        for d in dimensions:

            if not d.is_evaluated:
                continue

            impact_score = d.score * d.weight * 100

            if impact_score >= 60:
                impact = "HIGH"
            elif impact_score >= 30:
                impact = "MEDIUM"
            else:
                impact = "LOW"

            insights.append(
                DimensionInsight(
                    name=d.name,
                    score=d.score,
                    weight=d.weight,
                    impact=impact,
                )
            )

        return insights

    # ---------------------------------------------------------
    # BENCHMARK SEGMENT
    # ---------------------------------------------------------

    def build_percentile_segment(self, percentile: float) -> str:

        if percentile >= 90:
            return "Top 10%"
        elif percentile >= 75:
            return "Top 25%"
        elif percentile >= 50:
            return "Above Average"
        elif percentile >= 25:
            return "Below Average"
        return "Bottom 25%"

    # ---------------------------------------------------------
    # ROADMAP PRIORITY
    # ---------------------------------------------------------

    def prioritize_improvements(self, dims):

        roadmap = []

        for d in dims:

            if d.score is None:
                continue

            if d.name == "Communication" and d.score < 80:
                roadmap.append({
                    "priority": "HIGH",
                    "dimension": d.name,
                    "action": "Practice structured communication (STAR method) and improve clarity in technical explanations."
                })

            elif d.name == "Problem Solving" and d.score < 80:
                roadmap.append({
                    "priority": "HIGH",
                    "dimension": d.name,
                    "action": "Work on algorithmic problem solving and edge-case handling under time constraints."
                })

            elif d.name == "Technical Depth" and d.score < 80:
                roadmap.append({
                    "priority": "HIGH",
                    "dimension": d.name,
                    "action": "Deepen knowledge of system design, scalability, and real-world architecture patterns."
                })

        return roadmap
