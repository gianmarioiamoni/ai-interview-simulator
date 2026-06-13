# services/report_insight_builder.py

from typing import List, Dict, Optional
from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from domain.contracts.user.role import RoleType
from infrastructure.config.evaluation import (
    REPORT_IMPACT_HIGH_THRESHOLD,
    REPORT_IMPACT_MEDIUM_THRESHOLD,
    PERCENTILE_TOP_10,
    PERCENTILE_TOP_25,
    PERCENTILE_ABOVE_AVG,
    PERCENTILE_BELOW_AVG,
    NARRATIVE_DRIVER_SIGNAL_THRESHOLD,
    NARRATIVE_BLOCKER_SIGNAL_THRESHOLD,
    REPORT_IMPROVEMENT_PRIORITY_THRESHOLD,
)


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

            # Safety: evita None
            score = d.score or 0.0
            weight = d.weight or 0.0

            impact_score = score * weight * 100

            if impact_score >= REPORT_IMPACT_HIGH_THRESHOLD:
                impact = "HIGH"
            elif impact_score >= REPORT_IMPACT_MEDIUM_THRESHOLD:
                impact = "MEDIUM"
            else:
                impact = "LOW"

            insights.append(
                DimensionInsight(
                    name=d.name,
                    score=score,
                    weight=weight,
                    impact=impact,
                )
            )

        return insights

    # ---------------------------------------------------------
    # BENCHMARK SEGMENT
    # ---------------------------------------------------------

    def build_percentile_segment(self, percentile: float) -> str:

        if percentile >= PERCENTILE_TOP_10:
            return "Top 10%"
        elif percentile >= PERCENTILE_TOP_25:
            return "Top 25%"
        elif percentile >= PERCENTILE_ABOVE_AVG:
            return "Above Average"
        elif percentile >= PERCENTILE_BELOW_AVG:
            return "Below Average"
        return "Bottom 25%"

    def build_percentile_narrative(self, percentile: float, role: RoleType) -> str:
        role_label = self._format_role(role)

        if percentile >= PERCENTILE_TOP_10:
            return f"Top-tier {role_label}s in this range typically demonstrate exceptional technical depth, strong system design skills, and consistent high-quality performance across all areas."

        elif percentile >= PERCENTILE_TOP_25:
            return f"Strong {role_label}s in this range are strong performers, typically showing solid technical expertise and problem-solving ability, with minor areas for improvement."

        elif percentile >= PERCENTILE_ABOVE_AVG:
            return f"Above-average {role_label}s demonstrate good technical foundations and problem-solving skills, though some inconsistencies or weaker areas may still be present."

        elif percentile >= 40:
            return f"{role_label}s in this range show partial competency, but require improvement across multiple areas to meet hiring expectations."

        else:
            return f"{role_label}s below average typically exhibit significant gaps in key technical and communication skills required for the role."

    # ---------------------------------------------------------
    # SIGNAL INSIGHTS (🔥 CON SEVERITY)
    # ---------------------------------------------------------

    def build_signal_insights(self, signals: Dict[str, float]) -> List[Dict]:

        if not signals:
            return []

        insights: List[Dict] = []

        def severity(score: float) -> str:
            if score >= 0.7:
                return "🟢"
            elif score >= 0.4:
                return "🟡"
            return "🔴"

        ps = signals.get("problem_solving", 0.0)
        td = signals.get("technical_depth", 0.0)
        sd = signals.get("system_design")

        # -----------------------------
        # POSITIVE SIGNALS
        # -----------------------------

        if ps is not None and ps >= NARRATIVE_DRIVER_SIGNAL_THRESHOLD:
            insights.append(
                {
                    "text": "Strong problem-solving ability with high correctness.",
                    "severity": severity(ps),
                    "dimension": "problem_solving",
                    "score": round(ps, 2),
                }
            )

        if td is not None and td >= NARRATIVE_DRIVER_SIGNAL_THRESHOLD:
            insights.append(
                {
                    "text": "Solid technical implementation and code reliability.",
                    "severity": severity(td),
                    "dimension": "technical_depth",
                    "score": round(td, 2),
                }
            )

        # -----------------------------
        # NEGATIVE SIGNALS
        # -----------------------------

        if td is not None and td < NARRATIVE_BLOCKER_SIGNAL_THRESHOLD:
            insights.append(
                {
                    "text": "Struggles with technical implementation and runtime stability.",
                    "severity": severity(td),
                    "dimension": "technical_depth",
                    "score": round(td, 2),
                }
            )

        if ps is not None and ps < NARRATIVE_BLOCKER_SIGNAL_THRESHOLD:
            insights.append(
                {
                    "text": "Weak handling of edge cases and problem decomposition.",
                    "severity": severity(ps),
                    "dimension": "problem_solving",
                    "score": round(ps, 2),
                }
            )

        if sd is not None and sd < NARRATIVE_BLOCKER_SIGNAL_THRESHOLD:
            insights.append(
                {
                    "text": "Limited awareness of performance and system-level concerns.",
                    "severity": severity(sd),
                    "dimension": "system_design",
                    "score": round(sd, 2),
                }
            )

        return insights

    # ---------------------------------------------------------
    # ROADMAP PRIORITY
    # ---------------------------------------------------------

    def prioritize_improvements(self, dims: List[DimensionScoreDTO]):

        roadmap = []

        for d in dims:

            if d.score is None:
                continue

            if d.name == "Communication" and d.score < REPORT_IMPROVEMENT_PRIORITY_THRESHOLD:
                roadmap.append(
                    {
                        "priority": "HIGH",
                        "dimension": d.name,
                        "action": "Practice structured communication (STAR method) and improve clarity in technical explanations.",
                    }
                )

            elif d.name == "Problem Solving" and d.score < REPORT_IMPROVEMENT_PRIORITY_THRESHOLD:
                roadmap.append(
                    {
                        "priority": "HIGH",
                        "dimension": d.name,
                        "action": "Work on algorithmic problem solving and edge-case handling under time constraints.",
                    }
                )

            elif d.name == "Technical Depth" and d.score < REPORT_IMPROVEMENT_PRIORITY_THRESHOLD:
                roadmap.append(
                    {
                        "priority": "HIGH",
                        "dimension": d.name,
                        "action": "Deepen knowledge of system design, scalability, and real-world architecture patterns.",
                    }
                )

        return roadmap

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _format_role(self, role: RoleType) -> str:
        return role.value.replace("_", " ").title()
