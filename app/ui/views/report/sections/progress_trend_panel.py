# app/ui/views/report/sections/progress_trend_panel.py
# EPIC-V13-05 Phase 4 — C-23 ProgressTrendPanel (Plane B presentation only).
# EPIC-07 P5/C10 — insufficient-data uses empty.progress.insufficient catalog.

from __future__ import annotations

from html import escape

from app.ui.presentation.progress_surface import present_progress_surface
from app.ui.presentation.question_feedback_surface import surface_status_message
from domain.contracts.progress.learning_progress import (
    BehavioralTrend,
    FeatureTrend,
    LearningProgress,
    SessionProgressEntry,
)

# OI-DM-01 / F-W-02 — sole UI sufficiency gate (independent of LP-LP-03).
_UI_TREND_SESSION_THRESHOLD = 3

_TREND_COLORS: dict[str, tuple[str, str, str]] = {
    "improving": ("#15803d", "#f0fdf4", "#86efac"),
    "declining": ("#dc2626", "#fef2f2", "#fca5a5"),
    "stable": ("#2563eb", "#eff6ff", "#bfdbfe"),
    "insufficient_data": ("#64748b", "#f8fafc", "#e2e8f0"),
}

_TREND_LABELS: dict[str, str] = {
    "improving": "Improving",
    "declining": "Declining",
    "stable": "Stable",
    "insufficient_data": "Insufficient data",
}


def render_progress_trend_panel(learning_progress: LearningProgress) -> str:
    """Render ProgressTrendPanel from LearningProgress presentation fields only.

    Visibility gate (frozen): session_count >= 3.
    Does not compute trends; does not use has_sufficient_data as the UI gate.
    """
    has_sufficient = learning_progress.session_count >= _UI_TREND_SESSION_THRESHOLD
    surface = present_progress_surface(has_sufficient_sessions=has_sufficient)
    if not has_sufficient:
        return _render_insufficient_data(
            learning_progress.session_count,
            message=surface_status_message(surface),
        )

    return _render_trend(learning_progress)


def _render_insufficient_data(session_count: int, *, message: str) -> str:
    safe_message = escape(message)
    return f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:20px;" data-progress-state="insufficient-data">
<h2 style="margin:0 0 14px 0;color:#1e293b;">Progress Trend</h2>
<p style="color:#64748b;font-size:0.9em;margin:0 0 8px 0;">
{safe_message}
</p>
<p style="color:#94a3b8;font-size:0.85em;margin:0;">
{session_count} session{"s" if session_count != 1 else ""} recorded.
</p>
</div>
"""


def _render_trend(learning_progress: LearningProgress) -> str:
    markers_html = _render_session_markers(learning_progress.session_entries)
    trend_html = _render_behavioral_trend(learning_progress.behavioral_trend)

    return f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:20px;" data-progress-state="trend">
<h2 style="margin:0 0 14px 0;color:#1e293b;">Progress Trend</h2>
<p style="color:#64748b;font-size:0.9em;margin-bottom:16px;">
Cross-session behavioral progress based on {learning_progress.session_count} completed sessions.
</p>
{markers_html}
{trend_html}
</div>
"""


def _render_session_markers(session_entries: tuple[SessionProgressEntry, ...]) -> str:
    if not session_entries:
        return ""

    items = ""
    for entry in session_entries:
        items += (
            f'<span style="display:inline-block;margin:0 8px 8px 0;padding:4px 10px;'
            f'border-radius:6px;background:#e2e8f0;color:#334155;font-size:0.82em;">'
            f'Session {entry.session_index}'
            f'<span style="color:#64748b;margin-left:6px;">{entry.question_count} questions</span>'
            f"</span>"
        )

    return f"""
<div style="margin-bottom:16px;" data-progress-markers="session-entries">
<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:8px;">
Sessions
</div>
{items}
</div>
"""


def _render_behavioral_trend(behavioral_trend: BehavioralTrend | None) -> str:
    if behavioral_trend is None:
        return """
<div data-progress-trend="absent">
<p style="color:#64748b;font-size:0.9em;margin:0;">
No behavioral trend summary is available for these sessions.
</p>
</div>
"""

    overall = behavioral_trend.overall_trend_direction
    overall_label = _TREND_LABELS.get(overall, overall.replace("_", " ").title())
    text_color, _, _ = _TREND_COLORS.get(
        overall, _TREND_COLORS["insufficient_data"]
    )

    rows_html = ""
    for feature_trend in behavioral_trend.feature_trends:
        rows_html += _render_feature_trend_row(feature_trend)

    feature_block = (
        f'<div style="margin-top:14px;">{rows_html}</div>'
        if rows_html
        else ""
    )

    return f"""
<div data-progress-trend="behavioral" data-overall-trend="{escape(overall)}">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
  <span style="font-size:0.78em;font-weight:700;text-transform:uppercase;color:white;background:{text_color};padding:2px 8px;border-radius:4px;">
    Overall: {escape(overall_label)}
  </span>
  <span style="font-size:0.82em;color:#64748b;">
    {behavioral_trend.sessions_analysed} sessions analysed
  </span>
</div>
{feature_block}
</div>
"""


def _render_feature_trend_row(feature_trend: FeatureTrend) -> str:
    direction = feature_trend.trend_direction
    label = _TREND_LABELS.get(direction, direction.replace("_", " ").title())
    text_color, bg_color, border_color = _TREND_COLORS.get(
        direction, _TREND_COLORS["insufficient_data"]
    )
    feature_id = escape(feature_trend.feature_type_id)

    earliest = (
        f"{feature_trend.earliest_confidence:.0%}"
        if feature_trend.earliest_confidence is not None
        else "—"
    )
    latest = (
        f"{feature_trend.latest_confidence:.0%}"
        if feature_trend.latest_confidence is not None
        else "—"
    )

    return f"""
<div style="border:1px solid {border_color};border-radius:8px;padding:12px 14px;margin-bottom:10px;background:{bg_color};">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
  <span style="font-weight:600;color:#1e293b;font-size:0.95em;">{feature_id}</span>
  <span style="font-size:0.78em;font-weight:700;text-transform:uppercase;color:{text_color};">{escape(label)}</span>
  <span style="font-size:0.78em;color:#374151;">observed: {feature_trend.sessions_observed}</span>
</div>
<div style="font-size:0.85em;color:#475569;">
  Earliest confidence: {earliest} · Latest confidence: {latest}
</div>
</div>
"""
