# app/ui/views/report/sections/performance_section.py

from app.ui.views.report.charts.radar_chart import radar_chart


def render_performance(vm):

    report = vm["report"]

    radar = radar_chart(vm["names"], vm["scores"].copy())

    return f"""
<h2>Performance Overview</h2>

<table>
<tr>
<td width="50%">{radar}</td>
<td width="50%">
<strong>Strongest:</strong> {vm["strongest"].name if vm["strongest"] else '-'}<br>
<strong>Weakest:</strong> {vm["weakest"].name if vm["weakest"] else '-'}<br>
</td>
</tr>
</table>
"""
