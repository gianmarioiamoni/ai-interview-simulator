# app/ui/views/report/sections/coaching_section.py
# EPIC-V13-05 Phase 10 — renders CoachingSnapshot objectives from report.coaching_snapshot.

_PRIORITY_COLORS = {
    "critical": ("#dc2626", "#fef2f2", "#fca5a5"),
    "high":     ("#d97706", "#fffbeb", "#fcd34d"),
    "moderate": ("#2563eb", "#eff6ff", "#bfdbfe"),
    "low":      ("#16a34a", "#f0fdf4", "#86efac"),
}


def render_coaching_objectives(vm):
    """Render coaching objectives panel sourced from report.coaching_snapshot."""
    objectives = vm.get("coaching_objectives") or []

    if not objectives:
        return ""

    items_html = ""
    for obj in objectives:
        description = getattr(obj, "description", "")
        priority = getattr(obj, "priority", None)
        priority_val = priority.value if hasattr(priority, "value") else str(priority)
        confidence = getattr(obj, "confidence", None)
        feature_type = getattr(obj, "feature_type", None)
        feature_label = (
            feature_type.value.replace("_", " ").title()
            if hasattr(feature_type, "value")
            else str(feature_type) if feature_type else ""
        )

        text_color, bg_color, border_color = _PRIORITY_COLORS.get(
            priority_val, _PRIORITY_COLORS["moderate"]
        )

        confidence_html = (
            f'<span style="font-size:0.78em;color:#6b7280;margin-left:8px;">confidence: {confidence:.0%}</span>'
            if confidence is not None
            else ""
        )

        items_html += f"""
<div style="border:1px solid {border_color};border-radius:8px;padding:12px 14px;margin-bottom:10px;background:{bg_color};">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
  <span style="font-size:0.78em;font-weight:700;text-transform:uppercase;background:{text_color};color:white;padding:2px 7px;border-radius:4px;">{priority_val}</span>
  {f'<span style="font-size:0.82em;color:#475569;">{feature_label}</span>' if feature_label else ''}
  {confidence_html}
</div>
<div style="font-size:0.9em;color:#1e293b;">{description}</div>
</div>
"""

    return f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#15803d;">Coaching Objectives</h2>
<p style="color:#166534;font-size:0.9em;margin-bottom:16px;">
Targeted learning objectives identified from your interview performance.
</p>
{items_html}
</div>
"""
