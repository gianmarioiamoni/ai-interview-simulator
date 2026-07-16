# app/ui/views/report/sections/coaching_section.py
# EPIC-V13-05 Phase 10 — renders CoachingSnapshot objectives from report.coaching_snapshot.
# EPIC-06 C7 — coaching actions surface with inline origin from CoachingActionDTO (OF-01).

from html import escape

_PRIORITY_COLORS = {
    "critical": ("#dc2626", "#fef2f2", "#fca5a5"),
    "high":     ("#d97706", "#fffbeb", "#fcd34d"),
    "moderate": ("#2563eb", "#eff6ff", "#bfdbfe"),
    "low":      ("#16a34a", "#f0fdf4", "#86efac"),
}


def _format_label(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _render_action_origin(action) -> str:
    """Render OF-01 origin fields from CoachingActionDTO only."""
    origin_feature_type = getattr(action, "origin_feature_type", None)
    if not origin_feature_type:
        raise ValueError(
            "Coaching action missing origin_feature_type; refuse empty origin UI"
        )

    origin_supporting = getattr(action, "origin_supporting_observation_types", None)
    if origin_supporting is None:
        raise ValueError(
            "Coaching action missing origin_supporting_observation_types; "
            "refuse empty origin UI"
        )

    origin_objective_description = getattr(
        action, "origin_objective_description", None
    )
    if not origin_objective_description:
        raise ValueError(
            "Coaching action missing origin_objective_description; "
            "refuse empty origin UI"
        )

    feature_label = _format_label(str(origin_feature_type))
    if origin_supporting:
        observations_label = ", ".join(
            _format_label(str(item)) for item in origin_supporting
        )
    else:
        observations_label = "None"

    return f"""
<div style="margin-top:8px;font-size:0.82em;color:#475569;">
  <div style="margin-bottom:4px;">
    <span style="font-weight:600;color:#334155;">Origin:</span>
    <span style="margin-left:6px;">{escape(feature_label)}</span>
  </div>
  <div style="margin-bottom:4px;">
    <span style="font-weight:600;color:#334155;">Supporting observations:</span>
    <span style="margin-left:6px;">{escape(observations_label)}</span>
  </div>
  <div>
    <span style="font-weight:600;color:#334155;">Objective:</span>
    <span style="margin-left:6px;">{escape(str(origin_objective_description))}</span>
  </div>
</div>
"""


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


def render_coaching_actions(vm):
    """Render coaching actions panel with inline origin from CoachingActionDTO."""
    actions = vm.get("coaching_actions") or []

    if not actions:
        return ""

    items_html = ""
    for action in actions:
        description = getattr(action, "description", "")
        category = getattr(action, "category", None)
        category_val = category.value if hasattr(category, "value") else str(category)
        category_label = _format_label(category_val) if category_val else ""
        hours = getattr(action, "effort_estimate_hours", None)
        is_immediate = getattr(action, "is_immediate", False)

        effort_html = (
            f'<span style="font-size:0.78em;color:#6b7280;">{hours:.0f}h estimated</span>'
            if hours is not None
            else ""
        )
        immediate_html = (
            '<span style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            'background:#2563eb;color:white;padding:2px 7px;border-radius:4px;">Immediate</span>'
            if is_immediate
            else ""
        )
        origin_html = _render_action_origin(action)

        items_html += f"""
<div style="border:1px solid #bbf7d0;border-radius:8px;padding:12px 14px;margin-bottom:10px;background:#ffffff;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
  <span style="font-size:0.78em;font-weight:700;text-transform:uppercase;color:#15803d;background:#dcfce7;padding:2px 7px;border-radius:4px;">{escape(category_label)}</span>
  {immediate_html}
  {effort_html}
</div>
<div style="font-size:0.9em;color:#1e293b;">{escape(str(description))}</div>
{origin_html}
</div>
"""

    return f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:20px;margin-bottom:20px;">
<h2 style="margin:0 0 14px 0;color:#15803d;">Coaching Actions</h2>
<p style="color:#166534;font-size:0.9em;margin-bottom:16px;">
Concrete next steps linked to your learning objectives.
</p>
{items_html}
</div>
"""