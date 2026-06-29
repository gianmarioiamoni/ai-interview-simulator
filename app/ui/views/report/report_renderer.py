# app/ui/views/report/report_renderer.py

from .sections.overall_section import render_overall
from .sections.executive_section import render_executive
from .sections.decision_section import render_decision
from .sections.market_section import render_market
from .sections.performance_section import render_performance
from .sections.dimension_section import render_dimensions
from .sections.question_section import render_questions
from .sections.roadmap_section import render_roadmap
from .sections.signal_section import render_signals


class ReportRenderer:

    def render(self, vm):

        report = vm["report"]

        return f"""
<h1>AI Interview Evaluation</h1>

{render_overall(report)}
{render_executive(report)}
{render_performance(vm)}
{render_dimensions(vm)}
{render_questions(report)}
{render_market(vm)}
{render_decision(report)}
{render_roadmap(vm)}
{render_signals(vm)}
"""
