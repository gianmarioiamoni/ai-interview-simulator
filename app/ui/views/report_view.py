# -*- coding: utf-8 -*-
# app/ui/views/report_view.py

import io
import base64
import numpy as np
import matplotlib.pyplot as plt

from services.report_insight_builder import ReportInsightBuilder


# =========================================================
# Utility
# =========================================================


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;">'


# =========================================================
# Charts
# =========================================================


def _radar_chart(dimensions, scores):

    filtered = [(d, s) for d, s in zip(dimensions, scores) if s is not None]

    if not filtered:
        return "<i>No dimension data available</i>"

    dimensions, scores = zip(*filtered)

    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    scores = list(scores) + [scores[0]]
    angles = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.plot(angles, scores)
    ax.fill(angles, scores, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions)
    ax.set_ylim(0, 100)

    return _fig_to_base64(fig)


def _percentile_distribution(score, percentile, mean=63, std=14):

    x = np.linspace(mean - 4 * std, mean + 4 * std, 500)
    y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(x, y)
    ax.axvline(score, linestyle="--")

    ax.set_title("Role Distribution (Gaussian Model)")

    return _fig_to_base64(fig)


# =========================================================
# UI helpers
# =========================================================


def _badge(value, color):
    return f'<span style="background:{color};color:white;padding:6px 10px;border-radius:6px;font-size:12px;">{value}</span>'


def _score_badge(score):
    if score is None:
        return _badge("N/A", "#6b7280")
    if score >= 80:
        return _badge(f"{score}/100", "#16a34a")
    if score >= 60:
        return _badge(f"{score}/100", "#ca8a04")
    return _badge(f"{score}/100", "#dc2626")


def _test_progress_bar(passed, total):
    percent = (passed / total) * 100 if total else 0
    return f"""
<div style="margin-top:6px;">
<div style="background:#e5e7eb;height:10px;border-radius:5px;">
<div style="width:{percent}%;background:#16a34a;height:10px;border-radius:5px;"></div>
</div>
<div style="font-size:12px;">{passed}/{total} tests passed</div>
</div>
"""


def _confidence_bar(conf):
    percent = round(conf * 100, 1)
    return f"""
<div style="margin-top:8px;">
<strong>Confidence: {percent}%</strong>
<div style="background:#e5e7eb;height:10px;border-radius:5px;">
<div style="width:{percent}%;background:#16a34a;height:10px;border-radius:5px;"></div>
</div>
</div>
"""


# =========================================================
# Contribution table
# =========================================================


def _contribution_table(dimensions):

    rows = ""

    for d in dimensions:

        score = "N/A" if d.score is None else d.score

        status = (
            "⚪ N/A"
            if d.score is None
            else (
                "🟢 Strong"
                if d.score >= 80
                else "🟡 Medium" if d.score >= 60 else "🔴 Weak"
            )
        )

        rows += f"""
<tr>
<td>{d.name}</td>
<td>{score}</td>
<td>{d.weight if d.score else "-"}</td>
<td>{d.contribution if d.score else "-"}</td>
<td>{status}</td>
</tr>
"""

    return f"""
<table>
<tr>
<th>Dimension</th>
<th>Score</th>
<th>Weight</th>
<th>Contribution</th>
<th>Status</th>
</tr>
{rows}
</table>
"""


# =========================================================
# MAIN
# =========================================================


def build_report_markdown(report):

    print("DEBUG VIEW:", report.decision_explanation)

    dims = report.dimension_scores
    names = [d.name for d in dims]
    scores = [d.score for d in dims]

    valid = [d for d in dims if d.score is not None]

    strongest = max(valid, key=lambda x: x.score) if valid else None
    weakest = min(valid, key=lambda x: x.score) if valid else None

    radar = _radar_chart(names, scores.copy())
    gaussian = _percentile_distribution(report.overall_score, report.percentile_rank)

    decision_badge = _badge(report.hire_decision.upper(), "#2563eb")

    builder = ReportInsightBuilder()

    dimension_insights = builder.build_dimension_insights(dims)
    percentile_segment = builder.build_percentile_segment(report.percentile_rank)
    roadmap = builder.prioritize_improvements(dims)

    # ---------------- BUILD SAFE STRINGS
    drivers_html = "".join(
        f"<li>{d}</li>" for d in report.decision_explanation.get("drivers", [])
    )
    blockers_html = "".join(
        f"<li>{b}</li>" for b in report.decision_explanation.get("blockers", [])
    )

    roadmap_html = ""
    for r in roadmap:
        roadmap_html += f"""
<div style="margin-bottom:10px;">
<strong>[{r['priority']}] {r['dimension']}</strong><br>
{r['action']}
</div>
"""

    dimension_html = ""
    for d in dimension_insights:
        dimension_html += f"""
<div style="border:1px solid #ddd;padding:10px;margin-bottom:10px;border-radius:8px;">
<strong>{d.name}</strong> - {_score_badge(d.score)}<br>
Impact: <strong>{d.impact}</strong><br>
</div>
"""

    # ---------------- GATING

    gating_block = (
        f"<div style='color:#dc2626;font-weight:bold;'>Gating Triggered: {report.gating_reason}</div>"
        if report.gating_triggered
        else "<div style='color:#16a34a;font-weight:bold;'>No Gating Applied</div>"
    )

    # ---------------- MISSING

    missing_dims = [d.name for d in dims if d.score is None]

    missing_block = ""
    if missing_dims:
        missing_block = f"""
<div style="margin-top:20px;background:#fef3c7;padding:10px;">
<strong>Missing Evaluation</strong>
<ul>
{''.join(f"<li>{d}</li>" for d in missing_dims)}
</ul>
</div>
"""

    # ---------------- QUESTIONS

    question_block = ""

    for q in report.question_assessments:

        execution = ""

        if q.passed_tests is not None:
            execution += _test_progress_bar(q.passed_tests, q.total_tests)

        if q.execution_status:
            color = "#16a34a" if q.execution_status == "success" else "#dc2626"
            execution += f"<br>{_badge(q.execution_status.upper(), color)}"

        question_block += f"""
<div style="border:1px solid #ddd;padding:10px;margin-bottom:10px;border-radius:8px;">
<strong>Question {q.question_id}</strong><br>
Score: {_score_badge(q.score)}<br><br>
{q.feedback}
{execution}
</div>
"""

    # =========================================================
    # FINAL
    # =========================================================

    return f"""
<h1>AI Interview Final Evaluation</h1>

<h2>Executive Summary</h2>
<p>{report.executive_summary}</p>

<h2>Overall Performance</h2>

<table>
<tr>
<td><strong>Overall Score</strong><br>{_score_badge(report.overall_score)}</td>
<td><strong>Hiring Decision</strong><br>{decision_badge}</td>
<td><strong>Hiring Probability</strong><br>{_score_badge(report.hiring_probability)}</td>
</tr>
</table>

{gating_block}

<h2>Decision Rationale</h2>

<div style="margin-top:10px;">

<strong>Key Drivers</strong>
<ul>
{drivers_html}
</ul>

<strong>Blockers</strong>
<ul>
{blockers_html}
</ul>
</div>

<h2>Market Position</h2>

<p>
Candidate is positioned in <strong>{percentile_segment}</strong><br>
({_score_badge(report.percentile_rank)})
</p>

{gaussian}

<p>{report.percentile_explanation}</p>

<h2>Performance Overview</h2>

<table>
<tr>
<td width="50%">{radar}</td>
<td width="50%">
<strong>Strongest:</strong> {strongest.name if strongest else '-'}<br>
<strong>Weakest:</strong> {weakest.name if weakest else '-'}<br>
<strong>Total Tokens:</strong> {report.total_tokens_used}<br>
{_confidence_bar(report.confidence.final)}
</td>
</tr>
</table>

{_contribution_table(dims)}

{missing_block}

<h2>Dimension Analysis</h2>
{dimension_html}

<h2>Question-Level Assessment</h2>
{question_block}

<h2>Improvement Roadmap</h2>
{roadmap_html}
"""
