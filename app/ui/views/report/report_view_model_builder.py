# app/ui/views/report/report_view_model_builder.py
# EPIC-V13-05 Phase 10 — adds narrative_insights, coaching_objectives, study_recommendations.
# Phase 2 — study_recommendations from FinalReportDTO only (PC-05 / SR-02); no domain fallback.
# Phase 5 — LearningProgress injected separately (Plane B; never from FinalReportDTO).
# EPIC-06 C6 — narrative_insights from FinalReportDTO only (OF-01 / DTO-only UI).
# EPIC-06 C7 — coaching_actions from FinalReportDTO only (OF-01 / DTO-only UI).

from __future__ import annotations

from domain.contracts.progress.learning_progress import LearningProgress
from services.report_insight_builder import ReportInsightBuilder

from app.ui.presenters.helpers.dimension_ranking import DimensionRanking


class ReportViewModelBuilder:

    def build(
        self,
        report,
        learning_progress: LearningProgress | None = None,
    ):

        dims = report.dimension_scores
        strongest, weakest = DimensionRanking.compute(dims)

        builder = ReportInsightBuilder()

        # EPIC-06 C6 — narrative insights: FinalReportDTO only (OF-01 / DTO-only UI).
        # Empty list is valid; do not fall through to domain Report.narrative.insights.
        narrative_insights = list(getattr(report, "narrative_insights", ()))

        # Phase 10 — coaching objectives
        # FinalReportDTO carries pre-mapped CoachingObjectiveDTO list.
        # Domain Report carries CoachingSnapshot (fallback for direct Report rendering).
        coaching_objectives = list(
            getattr(report, "coaching_objectives", None)
            or (report.coaching_snapshot.collection.objectives if hasattr(report, "coaching_snapshot") else [])
        )

        # Phase 2 — study recommendations: FinalReportDTO only (PC-05 / SR-02 / F-W-03).
        # Empty list is valid; do not fall through to coaching_snapshot.
        study_recommendations = list(getattr(report, "study_recommendations", ()))

        # EPIC-06 C7 — coaching actions: FinalReportDTO only (OF-01 / DTO-only UI).
        # Empty list is valid; do not fall through to domain coaching_snapshot.actions.
        coaching_actions = list(getattr(report, "coaching_actions", ()))

        return {
            "report": report,
            "dims": dims,
            "names": [d.name for d in dims],
            "scores": [d.score for d in dims],
            "strongest": strongest,
            "weakest": weakest,
            "dimension_insights": builder.build_dimension_insights(dims),
            "percentile_segment": builder.build_percentile_segment(
                report.percentile_rank
            ),
            "percentile_narrative": builder.build_percentile_narrative(
                report.percentile_rank, report.role
            ),
            "roadmap": builder.prioritize_improvements(dims),
            "improvement_suggestions": getattr(report, "improvement_suggestions", None) or [],
            "missing_dims": [d.name for d in dims if d.score is None],
            "signal_insights": builder.build_signal_insights(
                report.dimension_signals
            ),
            "narrative_insights": narrative_insights,
            "coaching_objectives": coaching_objectives,
            "coaching_actions": coaching_actions,
            "study_recommendations": study_recommendations,
            # Plane B — separately injected; never mapped from FinalReportDTO (DM-FR-04).
            "learning_progress": learning_progress,
        }
