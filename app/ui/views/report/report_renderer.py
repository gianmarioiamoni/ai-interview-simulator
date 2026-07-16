# app/ui/views/report/report_renderer.py
# EPIC-V13-05 Phase 10 — adds narrative insights, coaching objectives, study recommendations.
# Phase 5 — compose ProgressTrendPanel from separately injected LearningProgress (Plane B).

from domain.contracts.progress.learning_progress import LearningProgress

from .sections.overall_section import render_overall
from .sections.executive_section import render_executive
from .sections.went_well_section import render_went_well
from .sections.held_you_back_section import render_held_you_back
from .sections.knowledge_gap_section import render_knowledge_gaps
from .sections.next_strategy_section import render_next_strategy
from .sections.decision_section import render_decision
from .sections.market_section import render_market
from .sections.performance_section import render_performance
from .sections.dimension_section import render_dimensions
from .sections.question_section import render_questions
from .sections.roadmap_section import render_roadmap
from .sections.signal_section import render_signals
from .sections.narrative_section import render_narrative
from .sections.coaching_section import render_coaching_objectives
from .sections.study_recommendations_section import render_study_recommendations
from .sections.progress_trend_panel import render_progress_trend_panel


class ReportRenderer:

    def render(self, vm):

        report = vm["report"]

        return f"""
<h1>AI Interview Evaluation</h1>

{render_overall(report)}
{render_executive(report)}
{render_went_well(report)}
{render_held_you_back(report)}
{render_knowledge_gaps(report)}
{render_next_strategy(report)}
{render_performance(vm)}
{render_dimensions(vm)}
{render_questions(report)}
{render_market(vm)}
{render_decision(report)}
{render_signals(vm)}
{render_narrative(vm)}
{render_coaching_objectives(vm)}
{render_study_recommendations(vm)}
{self._render_progress_trend(vm)}
"""

    def _render_progress_trend(self, vm) -> str:
        learning_progress = vm.get("learning_progress")
        if learning_progress is None:
            return ""
        if not isinstance(learning_progress, LearningProgress):
            raise TypeError(
                "vm['learning_progress'] must be LearningProgress or None "
                f"(got {type(learning_progress)!r})"
            )
        return render_progress_trend_panel(learning_progress)
