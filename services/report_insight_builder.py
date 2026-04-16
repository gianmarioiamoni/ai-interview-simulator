# app/ui/services/report_insight_builder.py

from typing import List
from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from domain.contracts.user.role import RoleType


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

    def build_percentile_narrative(self, percentile: float, role: RoleType) -> str:
        role_label = _format_role(role)

        if percentile >= 90:
            return f"Top-tier {role_label}s in this range typically demonstrate exceptional technical depth, strong system design skills, and consistent high-quality performance across all areas."

        elif percentile >= 75:
            return f"Strong {role_label}s in this range are strong performers, typically showing solid technical expertise and problem-solving ability, with minor areas for improvement."

        elif percentile >= 60:
            return f"Above-average {role_label}s demonstrate good technical foundations and problem-solving skills, though some inconsistencies or weaker areas may still be present."

        elif percentile >= 40:
            return f"{role_label}s in this range show partial competency, but require improvement across multiple areas to meet hiring expectations."

        else:
            return f"{role_label}s below average typically exhibit significant gaps in key technical and communication skills required for the role."

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


    def _format_role(self, role: RoleType) -> str:
        return role.value.replace("_", " ").title()
