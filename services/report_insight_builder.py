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

            impact_score = d.score * d.weight

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

    def prioritize_improvements(self, dimensions):

        weak = [d for d in dimensions if d.score is not None and d.score < 60]

        weak_sorted = sorted(weak, key=lambda x: x.score)

        roadmap = []

        for i, d in enumerate(weak_sorted):

            priority = "HIGH" if i < 2 else "MEDIUM"

            roadmap.append(
                {
                    "dimension": d.name,
                    "priority": priority,
                    "action": f"Improve {d.name} through targeted practice",
                }
            )

        return roadmap
