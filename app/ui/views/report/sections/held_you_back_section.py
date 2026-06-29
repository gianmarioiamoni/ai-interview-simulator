# app/ui/views/report/sections/held_you_back_section.py


def render_held_you_back(report):

    items = getattr(report, "held_you_back", []) or []

    if not items:
        return ""

    items_html = ""
    for item in items:
        behaviour = item.get("behaviour", "")
        why = item.get("why_it_matters", "")
        impact = item.get("impact", "")
        items_html += f"""
<div style="border-left:3px solid #f59e0b;padding:10px 14px;margin-bottom:14px;background:#fffbeb;border-radius:0 6px 6px 0;">
<div style="font-weight:600;color:#92400e;margin-bottom:4px;">{behaviour}</div>
<div style="font-size:0.9em;color:#78350f;margin-bottom:4px;"><strong>Why it matters:</strong> {why}</div>
<div style="font-size:0.9em;color:#92400e;"><strong>Evaluation impact:</strong> {impact}</div>
</div>
"""

    return f"""
<div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#92400e;">What Held You Back</h2>
{items_html}
</div>
"""
