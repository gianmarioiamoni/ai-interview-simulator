# app/ui/views/report/sections/narrative_section.py
# EPIC-V13-05 Phase 10 — renders NarrativeInsight list from report.narrative.insights.

_TYPE_COLORS = {
    "strength_signal": ("#15803d", "#f0fdf4", "#86efac"),
    "risk_signal":     ("#dc2626", "#fef2f2", "#fca5a5"),
    "growth_opportunity": ("#2563eb", "#eff6ff", "#bfdbfe"),
    "anomaly":         ("#d97706", "#fffbeb", "#fcd34d"),
}

_TYPE_LABELS = {
    "strength_signal": "Strength",
    "risk_signal": "Risk",
    "growth_opportunity": "Growth Opportunity",
    "anomaly": "Anomaly",
}


def render_narrative(vm):
    """Render narrative insights panel sourced from report.narrative.insights."""
    insights = vm.get("narrative_insights") or []

    if not insights:
        return ""

    items_html = ""
    for insight in insights:
        insight_type = getattr(insight, "insight_type", None)
        type_val = insight_type.value if hasattr(insight_type, "value") else str(insight_type)
        prose = getattr(insight, "prose", "")
        confidence = getattr(insight, "confidence", None)
        label = _TYPE_LABELS.get(type_val, type_val.replace("_", " ").title())
        text_color, bg_color, border_color = _TYPE_COLORS.get(type_val, ("#374151", "#f8fafc", "#e2e8f0"))

        confidence_html = (
            f'<span style="font-size:0.78em;color:#6b7280;margin-left:8px;">confidence: {confidence:.0%}</span>'
            if confidence is not None
            else ""
        )

        items_html += f"""
<div style="border-left:3px solid {border_color};padding:10px 14px;margin-bottom:10px;background:{bg_color};border-radius:0 6px 6px 0;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
  <span style="font-size:0.78em;font-weight:700;text-transform:uppercase;color:{text_color};background:{border_color};padding:2px 7px;border-radius:4px;">{label}</span>
  {confidence_html}
</div>
<div style="font-size:0.9em;color:#1e293b;">{prose}</div>
</div>
"""

    return f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#1e293b;">Narrative Insights</h2>
<p style="color:#64748b;font-size:0.9em;margin-bottom:16px;">
Evidence-grounded findings from your interview performance.
</p>
{items_html}
</div>
"""
