# app/ui/views/report/sections/overall_section.py

from app.ui.views.report.components.badges import score_badge, badge


def render_overall(report):

    decision_badge = badge(report.hire_decision.upper(), "#2563eb")

    gating_block = (
        f"<div style='color:#dc2626;font-weight:bold;'>Gating Triggered: {report.gating_reason}</div>"
        if report.gating_triggered
        else "<div style='color:#16a34a;font-weight:bold;'>No Gating Applied</div>"
    )

    return f"""
<h2>Overall Performance</h2>

<table>
<tr>
<td><strong>Overall Score</strong><br>{score_badge(report.overall_score)}</td>
<td><strong>Hiring Decision</strong><br>{decision_badge}</td>
<td><strong>Hiring Probability</strong><br>{score_badge(report.hiring_probability)}</td>
</tr>
</table>

{gating_block}
"""
