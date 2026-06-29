# app/ui/views/report/sections/went_well_section.py


def render_went_well(report):

    items = getattr(report, "went_well", []) or []

    if not items:
        return ""

    items_html = "".join(
        f"""<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;">
<span style="color:#16a34a;font-size:1.2em;flex-shrink:0;">✓</span>
<span style="color:#1e293b;">{item}</span>
</div>"""
        for item in items
    )

    return f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#15803d;">What You Did Well</h2>
{items_html}
</div>
"""
