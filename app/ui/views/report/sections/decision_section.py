# app/ui/views/report/sections/decision_section.py


def render_decision(report):

    drivers_html = "".join(
        f"<li>{d}</li>" for d in report.decision_explanation.get("drivers", [])
    )

    blockers_html = "".join(
        f"<li>{b}</li>" for b in report.decision_explanation.get("blockers", [])
    )

    return f"""
<h2>Decision Rationale</h2>

<div style="margin-top:10px; padding:10px; border:1px solid #e5e7eb; border-radius:6px;">

<strong>Key Drivers</strong>
<ul>
{drivers_html}
</ul>

<strong>Blockers</strong>
<ul>
{blockers_html}
</ul>

</div>
"""
