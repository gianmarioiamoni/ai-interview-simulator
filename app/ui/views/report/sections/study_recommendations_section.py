# app/ui/views/report/sections/study_recommendations_section.py
# EPIC-V13-05 Phase 2 — renders study recommendations from FinalReportDTO via view-model only.

_RESOURCE_ICONS = {
    "documentation": "📄",
    "exercise": "💻",
    "concept_review": "📖",
    "project": "🏗",
    "reading": "📚",
}


def render_study_recommendations(vm):
    """Render study recommendations panel from VM study_recommendations (DTO-sourced)."""
    recommendations = vm.get("study_recommendations") or []

    if not recommendations:
        return ""

    items_html = ""
    for rec in recommendations:
        topic = getattr(rec, "topic", "")
        rationale = getattr(rec, "rationale", "")
        resource_type = getattr(rec, "resource_type", None)
        resource_val = resource_type.value if hasattr(resource_type, "value") else str(resource_type)
        icon = _RESOURCE_ICONS.get(resource_val, "📌")
        label = resource_val.replace("_", " ").title()
        hours = getattr(rec, "estimated_duration_hours", None)
        duration_html = (
            f'<span style="font-size:0.78em;color:#6b7280;">{hours:.0f}h estimated</span>'
            if hours is not None
            else ""
        )

        items_html += f"""
<div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;margin-bottom:10px;background:#ffffff;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
  <span style="font-size:1em;">{icon}</span>
  <span style="font-size:0.82em;font-weight:700;text-transform:uppercase;color:#2563eb;">{label}</span>
  {duration_html}
</div>
<div style="font-weight:600;color:#1e293b;margin-bottom:4px;font-size:0.95em;">{topic}</div>
<div style="font-size:0.88em;color:#475569;">{rationale}</div>
</div>
"""

    return f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#1e293b;">Study Recommendations</h2>
<p style="color:#64748b;font-size:0.9em;margin-bottom:16px;">
Targeted resources to address your identified learning objectives.
</p>
{items_html}
</div>
"""
