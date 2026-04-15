# app/ui/views/report_view.py

import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional


# =========================================================
# Utility: Matplotlib → Base64
# =========================================================


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;">'


# =========================================================
# Radar Chart
# =========================================================


def _radar_chart(dimensions: list[str], scores: list[Optional[float]]) -> str:

    filtered = [
        (dim, score) for dim, score in zip(dimensions, scores) if score is not None
    ]

    if not filtered:
        return "<i>No dimension data available</i>"

    dimensions, scores = zip(*filtered)

    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    scores = list(scores) + [scores[0]]
    angles = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

    ax.plot(angles, scores, linewidth=2)
    ax.fill(angles, scores, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions)

    ax.set_ylim(0, 100)

    return _fig_to_base64(fig)


# =========================================================
# Percentile Gaussian Curve
# =========================================================


def _percentile_distribution(
    score: float, percentile: float, mean: float = 63, std: float = 14
) -> str:

    x = np.linspace(mean - 4 * std, mean + 4 * std, 500)
    y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)

    fig, ax = plt.subplots(figsize=(6, 3))

    ax.plot(x, y)
    ax.axvline(score, linestyle="--")

    ax.set_title("Role Distribution (Gaussian Model)")
    ax.set_xlabel("Score")
    ax.set_ylabel("Density")

    return _fig_to_base64(fig)


# =========================================================
# Score Badges
# =========================================================


def _badge(value: str, color: str) -> str:
    return f"""
<span style="
    background:{color};
    color:white;
    padding:6px 12px;
    border-radius:8px;
    font-weight:bold;
">
{value}
</span>
"""


def _score_badge(score: Optional[float]) -> str:
    if score is None:
        return _badge("NOT_EVALUATED", "#6b7280")

    if score >= 80:
        return _badge(f"{score}/100", "#16a34a")
    elif score >= 60:
        return _badge(f"{score}/100", "#ca8a04")
    return _badge(f"{score}/100", "#dc2626")


# =========================================================
# Confidence Bar
# =========================================================


def _confidence_bar(conf: float) -> str:
    percent = round(conf * 100, 1)

    if percent >= 80:
        color = "#16a34a"
    elif percent >= 60:
        color = "#ca8a04"
    else:
        color = "#dc2626"

    return f"""
<div style="margin-top:8px;">
    <div style="background:#e5e7eb;height:12px;border-radius:6px;">
        <div style="width:{percent}%;background:{color};height:12px;border-radius:6px;"></div>
    </div>
    <div style="margin-top:4px;font-size:13px;">Confidence: {percent}%</div>
</div>
"""


# =========================================================
# Test Progress Bar
# =========================================================


def _test_progress_bar(passed: int, total: int) -> str:

    percent = (passed / total) * 100 if total else 0
    color = "#16a34a" if passed == total else "#ca8a04"

    return f"""
<div style="margin-top:6px;">
    <div style="background:#e5e7eb;height:12px;border-radius:6px;">
        <div style="width:{percent}%;background:{color};height:12px;border-radius:6px;"></div>
    </div>
    <div style="margin-top:4px;font-size:13px;">
        {passed} / {total} tests passed
    </div>
</div>
"""


# =========================================================
# Contribution Table
# =========================================================


def _contribution_table(dimensions) -> str:

    if not dimensions:
        return "<i>No contribution data available</i>"

    rows = ""

    for d in dimensions or []:
        score_display = "NOT_EVALUATED" if d.score is None else f"{d.score}"
        weight_display = "-" if d.score is None else f"{d.weight}"
        contribution_display = "-" if d.score is None else f"{d.contribution}"

        rows += f"""
            <tr>
                <td>{d.name}</td>
                <td>{score_display}</td>
                <td>{weight_display}</td>
                <td><strong>{contribution_display}</strong></td>
            </tr>
        """

    return f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <th align="left">Dimension</th>
                <th>Score</th>
                <th>Weight</th>
                <th>Contribution</th>
            </tr>
            {rows}
        </table>
    """


# =========================================================
# MAIN RENDER
# =========================================================


def build_report_markdown(report) -> str:

    dimensions = [d.name for d in report.dimension_scores]
    scores = [d.score for d in report.dimension_scores]

    valid_dimensions = [d for d in report.dimension_scores if d.score is not None]

    strongest = (
        max(valid_dimensions, key=lambda x: x.score) if valid_dimensions else None
    )
    weakest = min(valid_dimensions, key=lambda x: x.score) if valid_dimensions else None

    radar_img = _radar_chart(dimensions, scores.copy())
    gaussian_img = _percentile_distribution(
        report.overall_score, report.percentile_rank
    )

    decision_color = {
        "hire": "#16a34a",
        "lean_hire": "#65a30d",
        "lean_no_hire": "#ca8a04",
        "no_hire": "#dc2626",
    }

    decision_badge = _badge(
        report.hire_decision.upper(),
        decision_color.get(report.hire_decision, "#6b7280"),
    )

    # ---------------- Decision reasons (HTML)
    if report.decision_reasons:
        decision_reasons_block = (
            "<ul>"
            + "".join([f"<li>{r}</li>" for r in report.decision_reasons])
            + "</ul>"
        )
    else:
        decision_reasons_block = "<i>No specific decision rationale available.</i>"

    # ---------------- Questions (HTML)
    question_block = ""

    for q in report.question_assessments:

        execution_block = ""

        if q.passed_tests is not None and q.total_tests is not None:
            execution_block += f"""
<strong>Test Results</strong>
{_test_progress_bar(q.passed_tests, q.total_tests)}
"""

        if q.execution_status:
            status_color = "#16a34a" if q.execution_status == "success" else "#dc2626"

            execution_block += f"""
<br>
<strong>Execution Status:</strong> {_badge(q.execution_status.upper(), status_color)}
"""

        question_block += f"""
<h3>Question {q.question_id}</h3>
<div>Score: {_score_badge(q.score)}</div>
<p>{q.feedback}</p>
{execution_block}
"""

    # ---------------- Improvements (HTML)
    if report.improvement_suggestions:
        improvements = (
            "<ul>"
            + "".join([f"<li>{i}</li>" for i in report.improvement_suggestions])
            + "</ul>"
        )
    else:
        improvements = "<i>No major improvement areas identified.</i>"

    # ---------------- Gating
    gating_block = (
        f"<div style='color:#dc2626;font-weight:bold;'>🚨 Gating Triggered: {report.gating_reason}</div>"
        if report.gating_triggered
        else "<div style='color:#16a34a;font-weight:bold;'>✅ No Gating Applied</div>"
    )

    # ---------------- Missing dimensions
    missing_dims = [d.name for d in report.dimension_scores if d.score is None]

    missing_block = ""
    if missing_dims:
        missing_block = f"""
        <div style="margin-top:20px; padding:12px; border-radius:8px; background:#fef3c7; color:#92400e;">
            <strong>⚠️ Missing Evaluation</strong><br>
            The following dimensions were not assessed:
            <ul>
                {''.join(f"<li>{d}</li>" for d in missing_dims)}
            </ul>
        </div>
        """

    # =========================================================
    # FINAL HTML
    # =========================================================

    return f"""
<h1>🧠 AI Interview Final Evaluation</h1>
<hr>

<h2>📊 Executive Summary</h2>
<p>{report.executive_summary}</p>

<hr>

<h2>🎯 Overall Performance</h2>

<div>Overall Score: {_score_badge(report.overall_score)}</div>
<div><strong>Hiring Decision:</strong> {decision_badge}</div>
<div>Hiring Probability: {_score_badge(report.hiring_probability)}</div>

{gating_block}

<hr>

<h2>🧾 Decision Rationale</h2>
{decision_reasons_block}

<hr>

<h2>📈 Percentile Ranking</h2>
{gaussian_img}

<div>Percentile: {_score_badge(report.percentile_rank)}</div>
<p>{report.percentile_explanation}</p>

<hr>

<h2>🧭 Performance Overview</h2>

<div style="display:flex; gap:40px;">

<div style="flex:1;">
<h4>Dimension Breakdown</h4>
{radar_img}

<h4>Weighted Contribution</h4>
{_contribution_table(report.dimension_scores)}
</div>

<div style="flex:1;">
<h4>Highlights</h4>

{"<i>No dimension data available</i>" if not strongest else f'''
<strong>Strongest Dimension:</strong><br>
{_badge(strongest.name, "#16a34a")}  
Score: {strongest.score}/100

<br><br>

<strong>Weakest Dimension:</strong><br>
{_badge(weakest.name, "#dc2626")}  
Score: {weakest.score}/100
'''}

<br><br>

<strong>Total Tokens Used:</strong> {report.total_tokens_used}

{_confidence_bar(report.confidence.final)}

</div>

</div>

{missing_block}

<hr>

<h2>📝 Question-Level Assessment</h2>
{question_block}

<hr>

<h2>🚀 Improvement Roadmap</h2>
{improvements}

<hr>

<small>
This evaluation combines deterministic scoring, role-weighted modeling, statistical percentile estimation,
and AI-generated qualitative justification.
</small>
"""
