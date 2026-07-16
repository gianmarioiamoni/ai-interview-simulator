# app/ui/replay/replay_html_composer.py

from __future__ import annotations

from html import escape

from app.ui.replay.panels.replay_coaching_panel import (
    CoachingViewModel,
    ReplayCoachingPanel,
)
from app.ui.replay.panels.replay_error_boundary import (
    ErrorViewModel,
    ReplayErrorBoundary,
)
from app.ui.replay.panels.replay_navigation_bar import (
    NavigationViewModel,
    ReplayNavigationBar,
)
from app.ui.replay.panels.replay_question_panel import (
    QuestionViewModel,
    ReplayQuestionPanel,
)
from app.ui.replay.panels.replay_scoring_panel import (
    ReplayScoringPanel,
    ScoringViewModel,
)
from app.ui.replay.panels.replay_session_summary_panel import (
    ReplaySessionSummaryPanel,
    SessionSummaryViewModel,
)
from app.ui.replay.replay_view_controller import ReplayViewController
from domain.contracts.replay.replay_session import ReplaySession


def compose_navigation_html(model: NavigationViewModel) -> str:
    return f"<p class='replay-nav-label'>{escape(model.display_label)}</p>"


def compose_summary_html(model: SessionSummaryViewModel) -> str:
    rows = [
        f"<li><strong>Session</strong>: {model.interview_index}</li>",
        f"<li><strong>Date</strong>: {escape(model.session_date_display)}</li>",
        f"<li><strong>Role</strong>: {escape(model.role)}</li>",
        f"<li><strong>Seniority</strong>: {escape(model.seniority_level)}</li>",
        f"<li><strong>Mode</strong>: {escape(model.interview_mode)}</li>",
        f"<li><strong>Questions</strong>: {model.question_count}</li>",
    ]
    if model.duration_display is not None:
        rows.append(f"<li><strong>Duration</strong>: {escape(model.duration_display)}</li>")
    if model.company is not None:
        rows.append(f"<li><strong>Company</strong>: {escape(model.company)}</li>")
    if model.has_scoring:
        rows.append(f"<li><strong>Score</strong>: {model.overall_score}</li>")
        if model.hire_decision is not None:
            rows.append(
                f"<li><strong>Hire decision</strong>: " f"{escape(model.hire_decision.value)}</li>"
            )
        if model.level is not None:
            rows.append(f"<li><strong>Level</strong>: {escape(model.level.value)}</li>")
    elif model.score_unavailable_label is not None:
        rows.append(f"<li><em>{escape(model.score_unavailable_label)}</em></li>")
    return (
        "<section class='replay-summary'><h3>Session Summary</h3><ul>"
        + "".join(rows)
        + "</ul></section>"
    )


def compose_question_html(model: QuestionViewModel) -> str:
    parts = [
        "<section class='replay-question'>",
        f"<p><strong>Q{model.question_index + 1}</strong> · "
        f"{escape(model.question_type)} · {escape(model.area_label)}</p>",
        f"<p>{escape(model.question_prompt)}</p>",
        f"<p><strong>Answer</strong>: {escape(model.answer_display)}</p>",
        f"<p><strong>Score</strong>: {model.score} / {model.max_score} "
        f"({model.score_pct:.0f}%)</p>",
        f"<p><strong>Feedback</strong>: {escape(model.feedback)}</p>",
        f"<p><strong>Attempts</strong>: {model.attempts}</p>",
    ]
    if model.strengths:
        items = "".join(f"<li>{escape(s)}</li>" for s in model.strengths)
        parts.append(f"<p><strong>Strengths</strong></p><ul>{items}</ul>")
    if model.weaknesses:
        items = "".join(f"<li>{escape(w)}</li>" for w in model.weaknesses)
        parts.append(f"<p><strong>Weaknesses</strong></p><ul>{items}</ul>")
    if model.follow_up_question is not None:
        parts.append(f"<p><strong>Follow-up</strong>: {escape(model.follow_up_question)}</p>")
    if model.has_hint:
        parts.append(
            "<p><strong>AI Hint</strong>: "
            f"{escape(model.ai_hint_explanation or '')} "
            f"{escape(model.ai_hint_suggestion or '')}</p>"
        )
    if model.execution_result is not None:
        er = model.execution_result
        parts.append(
            "<div class='replay-execution'>"
            f"<p><strong>Execution</strong>: {escape(er.status_badge)}</p>"
            f"<p>Tests: {er.passed_tests}/{er.total_tests} "
            f"({er.pass_rate_pct:.0f}%)</p>"
            "</div>"
        )
    parts.append("</section>")
    return "".join(parts)


def compose_scoring_html(model: ScoringViewModel | None) -> str:
    if model is None:
        return ""
    dims = "".join(
        f"<li>{escape(name)}: {score}</li>" for name, score in model.dimension_scores.items()
    )
    gating = ""
    if model.gating_triggered and model.gating_reason is not None:
        gating = f"<p><strong>Gating</strong>: {escape(model.gating_reason)}</p>"
    return (
        "<section class='replay-scoring'><h3>Scoring</h3>"
        f"<p>Overall: {model.overall_score}</p>"
        f"<p>Hire: {escape(model.hire_decision.value)}</p>"
        f"<p>Level: {escape(model.level.value)}</p>"
        f"<p>Hiring probability: {model.hiring_probability}</p>"
        f"<p>Percentile: {model.percentile_rank} — "
        f"{escape(model.percentile_explanation)}</p>"
        f"<ul>{dims}</ul>{gating}</section>"
    )


def compose_coaching_html(model: CoachingViewModel) -> str:
    insights = (
        f"<p><em>{escape(model.narrative_empty_label)}</em></p>"
        if model.narrative_empty_label
        else "<ul>"
        + "".join(f"<li>{escape(i.prose)}</li>" for i in model.narrative_insights)
        + "</ul>"
    )
    objectives = (
        f"<p><em>{escape(model.coaching_empty_label)}</em></p>"
        if model.coaching_empty_label
        else "<ul>"
        + "".join(f"<li>{escape(o.description)}</li>" for o in model.coaching_objectives)
        + "</ul>"
    )
    recommendations = ""
    if model.coaching_recommendations:
        recommendations = (
            "<p><strong>Recommendations</strong></p><ul>"
            + "".join(
                f"<li>{escape(r.topic)} — {escape(r.rationale)}</li>"
                for r in model.coaching_recommendations
            )
            + "</ul>"
        )
    overview = ""
    if model.overview_prose is not None:
        overview = (
            f"<p><strong>{escape(model.overview_label)}</strong>: "
            f"{escape(model.overview_prose)}</p>"
        )
    return (
        "<section class='replay-coaching'>"
        f"<h3>{escape(model.section_a_label)}</h3>{overview}{insights}"
        f"<h3>{escape(model.section_b_label)}</h3>{objectives}{recommendations}"
        "</section>"
    )


def compose_error_html(model: ErrorViewModel) -> str:
    return (
        "<section class='replay-error-content'>"
        f"<p>{escape(model.candidate_message)}</p>"
        f"<p><strong>{escape(model.action_label)}</strong></p>"
        "</section>"
    )


def compose_success_panels(
    controller: ReplayViewController,
) -> dict[str, str | NavigationViewModel]:
    session: ReplaySession = controller.session
    nav = ReplayNavigationBar(session.timeline, controller.current_position).render()
    summary = ReplaySessionSummaryPanel(session).render()
    question = ReplayQuestionPanel(controller.current_record).render()
    scoring = ReplayScoringPanel(session).render()
    coaching = ReplayCoachingPanel(session).render()
    return {
        "nav": nav,
        "nav_html": compose_navigation_html(nav),
        "summary_html": compose_summary_html(summary),
        "question_html": compose_question_html(question),
        "scoring_html": compose_scoring_html(scoring),
        "coaching_html": compose_coaching_html(coaching),
        "error_html": "",
    }


def compose_error_panel(boundary: ReplayErrorBoundary) -> str:
    return compose_error_html(boundary.render())
