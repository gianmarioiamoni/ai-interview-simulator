# app/ui/views/report/sections/dimension_section.py

from app.ui.views.report.components.badges import score_badge
from app.ui.views.report.components.tables import contribution_table


def render_dimensions(vm):

    dims = vm["dims"]

    # ---------------- MISSING

    missing_block = ""
    if vm["missing_dims"]:
        missing_block = f"""
<div style="margin-top:20px;background:#fef3c7;padding:10px;">
<strong>Missing Evaluation</strong>
<ul>
{''.join(f"<li>{d}</li>" for d in vm["missing_dims"])}
</ul>
</div>
"""

    # ---------------- DIMENSION INSIGHTS

    dimension_html = ""
    for d in vm["dimension_insights"]:
        dimension_html += f"""
<div style="border:1px solid #ddd;padding:10px;margin-bottom:10px;border-radius:8px;">
<strong>{d.name}</strong> - {score_badge(d.score)}<br>
Impact: <strong>{d.impact}</strong><br>
</div>
"""

    return f"""
{contribution_table(dims)}

{missing_block}

<h2>Dimension Analysis</h2>
{dimension_html}
"""
