# app/ui/views/report/sections/next_strategy_section.py

_IMPACT_COLORS = {
    "High":   ("#dc2626", "#fef2f2", "#fca5a5"),
    "Medium": ("#d97706", "#fffbeb", "#fcd34d"),
    "Low":    ("#16a34a", "#f0fdf4", "#86efac"),
}


def render_next_strategy(report):

    items = getattr(report, "next_strategy", []) or []

    if not items:
        return ""

    items_html = ""
    for i, item in enumerate(items[:3], start=1):
        priority = item.get("priority", f"Priority {i}")
        why = item.get("why", "")
        improvement = item.get("expected_improvement", "")
        impact = item.get("impact", "Medium")

        text_color, bg_color, border_color = _IMPACT_COLORS.get(
            impact, _IMPACT_COLORS["Medium"]
        )

        items_html += f"""
<div style="border:1px solid {border_color};border-radius:8px;padding:14px;margin-bottom:12px;background:{bg_color};">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
  <span style="background:#1e293b;color:white;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:0.8em;font-weight:bold;flex-shrink:0;">{i}</span>
  <span style="font-weight:700;color:#1e293b;font-size:1em;">{priority}</span>
  <span style="margin-left:auto;background:{text_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.78em;font-weight:600;">{impact} Impact</span>
</div>
<div style="font-size:0.9em;color:#374151;margin-bottom:4px;"><strong>Why:</strong> {why}</div>
<div style="font-size:0.9em;color:#374151;"><strong>What will improve:</strong> {improvement}</div>
</div>
"""

    return f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#1e293b;">Next Interview Strategy</h2>
<p style="color:#64748b;font-size:0.9em;margin-bottom:16px;">
Three priorities to focus on before your next interview.
</p>
{items_html}
</div>
"""
