# app/ui/views/report/sections/overall_section.py

from app.ui.views.report.components.badges import score_badge, badge, score_band_badge
from app.ui.mappers.hire_decision_mapper import HireDecisionMapper
from domain.contracts.interview.hire_decision import HireDecision


def _parse_decision(report) -> HireDecision | None:
    """Resolve HireDecision enum from report, which may store a string label."""
    hd = getattr(report, "_hire_decision_enum", None)
    if hd is not None:
        return hd
    label_to_enum = {
        "Hire": HireDecision.HIRE,
        "Lean Hire": HireDecision.LEAN_HIRE,
        "Lean No Hire": HireDecision.LEAN_NO_HIRE,
        "No Hire": HireDecision.NO_HIRE,
    }
    raw = getattr(report, "hire_decision", "")
    return label_to_enum.get(raw)


def render_overall(report):

    decision_enum = _parse_decision(report)

    readiness_label = (
        HireDecisionMapper.to_readiness_label(decision_enum)
        if decision_enum
        else report.hire_decision
    )
    readiness_color = (
        HireDecisionMapper.to_readiness_color(decision_enum)
        if decision_enum
        else "#4b5563"
    )

    seniority_label = getattr(report, "seniority_level", "mid").capitalize()
    role_label = getattr(report, "role", "").value if hasattr(getattr(report, "role", ""), "value") else str(getattr(report, "role", ""))

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
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:20px;">

<h2 style="margin:0 0 4px 0;font-size:1.1em;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Interview Readiness</h2>

<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:16px;">
  <span style="background:{readiness_color};color:white;padding:8px 18px;border-radius:8px;font-size:1.1em;font-weight:bold;">
    {readiness_label}
  </span>
  <div>
    <span style="font-size:2em;font-weight:bold;color:#1e293b;">{report.overall_score:.0f}</span>
    <span style="font-size:1em;color:#64748b;"> /100</span>
    &nbsp;&nbsp;{score_band_badge(report.overall_score)}
  </div>
</div>

<div style="color:#64748b;font-size:0.9em;">
  {seniority_label} · {role_label.replace("_", " ").title()}
</div>

{context_block}
</div>
"""
