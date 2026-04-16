# app/ui/views/report/sections/performance_section.py

from ..charts.radar_chart import radar_chart
from ..components.bars import confidence_bar


def render_performance(vm):

    report = vm["report"]

    radar = radar_chart(vm["names"], vm["scores"])

    return f"""
<h2>Performance Overview</h2>

<table>
<tr>
<td width="50%">{radar}</td>
<td width="50%">
<strong>Strongest:</strong> {vm["strongest"].name if vm["strongest"] else '-'}<br>
<strong>Weakest:</strong> {vm["weakest"].name if vm["weakest"] else '-'}<br>
{confidence_bar(report.confidence.final)}
</td>
</tr>
</table>
"""
