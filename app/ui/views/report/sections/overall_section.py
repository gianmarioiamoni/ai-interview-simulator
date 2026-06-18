# app/ui/views/report/sections/overall_section.py

from app.ui.views.report.components.badges import score_badge, badge
from app.ui.mappers.gating_reason_mapper import map_gating_reason


def render_overall(report):

    decision_badge = badge(report.hire_decision.upper(), "#2563eb")

    # -----------------------------------------------------
    # SCORE DISPLAY 
    # -----------------------------------------------------

    if report.raw_score != report.adjusted_score:
        score_block = f"""
        {score_badge(report.adjusted_score)}
        <div style='font-size:12px;color:#6b7280'>
            Base: {report.raw_score:.1f}
        </div>
        """
    else:
        score_block = score_badge(report.overall_score)

    # -----------------------------------------------------
    # GATING
    # -----------------------------------------------------

    if report.gating_triggered:
        gating_block = f"""
        <div style='color:#dc2626;font-weight:bold;'>
            Gating Applied: {map_gating_reason(report.gating_reason)}
        </div>
        """
    else:
        gating_block = """
        <div style='color:#16a34a;font-weight:bold;'>
            No Gating Applied
        </div>
        """

    seniority_label = getattr(report, "seniority_level", "mid").capitalize()

    context_profile = getattr(report, "context_profile", None)
    context_block = ""
    if context_profile is not None:
        _MAX = 300
        jd = context_profile.job_description
        cd = context_profile.company_description
        bc = getattr(context_profile, "business_context", None)
        if jd or cd or bc:
            jd_line = ""
            cd_line = ""
            bc_line = ""
            if bc:
                bc_line = f"<div><strong>Business Context:</strong> {bc.value.capitalize()}</div>"
            if jd:
                jd_preview = jd[:_MAX] + ("…" if len(jd) > _MAX else "")
                jd_line = f"<div><strong>Job Description:</strong> {jd_preview}</div>"
            if cd:
                cd_preview = cd[:_MAX] + ("…" if len(cd) > _MAX else "")
                cd_line = f"<div><strong>Company Description:</strong> {cd_preview}</div>"
            context_block = f"""
<details>
<summary><strong>Interview Context</strong></summary>
{bc_line}
{jd_line}
{cd_line}
</details>
"""

    return f"""
<h2>Overall Performance</h2>

<table>
<tr>
<td><strong>Overall Score</strong><br>{score_block}</td>
<td><strong>Hiring Decision</strong><br>{decision_badge}</td>
<td><strong>Hiring Confidence Score</strong><br>{score_badge(report.hiring_probability)}</td>
<td><strong>Seniority Level</strong><br>{seniority_label}</td>
</tr>
</table>

{gating_block}
{context_block}
"""
