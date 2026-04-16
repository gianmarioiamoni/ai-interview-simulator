# app/ui/views/report/report_view_model_builder.py

from services.report_insight_builder import ReportInsightBuilder


class ReportViewModelBuilder:

    def build(self, report):

        dims = report.dimension_scores
        valid = [d for d in dims if d.score is not None]

        builder = ReportInsightBuilder()

        return {
            "report": report,
            "dims": dims,
            "names": [d.name for d in dims],
            "scores": [d.score for d in dims],
            "strongest": max(valid, key=lambda x: x.score) if valid else None,
            "weakest": min(valid, key=lambda x: x.score) if valid else None,
            "dimension_insights": builder.build_dimension_insights(dims),
            "percentile_segment": builder.build_percentile_segment(
                report.percentile_rank
            ),
            "percentile_narrative": builder.build_percentile_narrative(
                report.percentile_rank, report.role
            ),
            "roadmap": builder.prioritize_improvements(dims),
            "missing_dims": [d.name for d in dims if d.score is None],
        }
