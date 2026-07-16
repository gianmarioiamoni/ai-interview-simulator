# app/ui/views/report/report_view_model_builder.py
# EPIC-V13-05 Phase 10 — adds narrative_insights, coaching_objectives, study_recommendations.
# Phase 2 — study_recommendations from FinalReportDTO only (PC-05 / SR-02); no domain fallback.

from services.report_insight_builder import ReportInsightBuilder

from app.ui.presenters.helpers.dimension_ranking import DimensionRanking


class ReportViewModelBuilder:

    def build(self, report):

        dims = report.dimension_scores
        strongest, weakest = DimensionRanking.compute(dims)

        builder = ReportInsightBuilder()

        # Phase 10 — narrative insights (FinalReportDTO carries pre-mapped DTOs;
        # domain Report carries NarrativeInsight objects; both are supported via getattr).
        narrative_insights = list(
            getattr(report, "narrative_insights", None)
            or (report.narrative.insights if hasattr(report, "narrative") else [])
        )

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
            "study_recommendations": study_recommendations,
        }
