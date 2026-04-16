# app/ui/views/report/sections/market_section.py

from app.ui.views.report.charts.distribution_chart import percentile_distribution
from app.ui.views.report.components.badges import score_badge


def render_market(vm):

    report = vm["report"]

    gaussian = percentile_distribution(report.overall_score)

    return f"""
<h2>Market Position</h2>

<p>
Candidate is positioned in <strong>{vm["percentile_segment"]}</strong><br>
({score_badge(report.percentile_rank)})
</p>

{gaussian}

<p style="color:#6b7280;font-size:12px;">
{report.percentile_explanation}
</p>

<div style="margin-top:10px;padding:10px;border-left:4px solid #2563eb;">
{vm["percentile_narrative"]}
</div>
"""
