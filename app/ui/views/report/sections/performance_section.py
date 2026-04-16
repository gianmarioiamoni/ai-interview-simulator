# app/ui/views/report/sections/performance_section.py

from app.ui.views.report.charts.radar_chart import radar_chart
from app.ui.views.report.components.bars import confidence_bar


def _build_confidence_text(conf):

    if conf > 0.85:
        base = "High confidence (consistent performance)"
    elif conf > 0.65:
        base = "Moderate confidence (some variability)"
    else:
        base = "Low confidence (inconsistent performance)"

    return f"{base} — based on score consistency across evaluated dimensions"


def render_performance(vm):

    report = vm["report"]

    radar = radar_chart(vm["names"], vm["scores"].copy())

    confidence_text = _build_confidence_text(report.confidence.final)

    return f"""
<h2>Performance Overview</h2>

<table>
<tr>
<td width="50%">{radar}</td>
<td width="50%">
<strong>Strongest:</strong> {vm["strongest"].name if vm["strongest"] else '-'}<br>
<strong>Weakest:</strong> {vm["weakest"].name if vm["weakest"] else '-'}<br>
<strong>Total Tokens:</strong> {report.total_tokens_used}<br>

<strong>{confidence_text}</strong><br>
{confidence_bar(report.confidence.final)}

</td>
</tr>
</table>
"""
