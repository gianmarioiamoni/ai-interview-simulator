# app/ui/views/report_view.py

import io
import base64
import math
import numpy as np
import matplotlib.pyplot as plt


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


def _radar_chart(dimensions: list[str], scores: list[float]) -> str:

    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    scores += scores[:1]
    angles += angles[:1]

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


def _score_badge(score: float) -> str:
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
# MAIN RENDER
# =========================================================


def build_report_markdown(report) -> str:

    dimensions = [d.name for d in report.dimension_scores]
    scores = [d.score for d in report.dimension_scores]

    strongest = max(report.dimension_scores, key=lambda x: x.score)
    weakest = min(report.dimension_scores, key=lambda x: x.score)

    radar_img = _radar_chart(dimensions, scores.copy())
    gaussian_img = _percentile_distribution(
        report.overall_score, report.percentile_rank
    )

    question_block = ""
    for q in report.question_assessments:
        question_block += f"""
### Question {q.question_id}

Score: {_score_badge(q.score)}

{q.feedback}
"""

    improvements = "\n".join([f"- {i}" for i in report.improvement_suggestions])

    gating_block = (
        f"<div style='color:#dc2626;font-weight:bold;'>🚨 Gating Triggered: {report.gating_reason}</div>"
        if report.gating_triggered
        else "<div style='color:#16a34a;font-weight:bold;'>✅ No Gating Applied</div>"
    )

    return f"""
# 🧠 AI Interview Final Evaluation

---

## 📊 Executive Summary
{report.executive_summary}

---

## 🎯 Overall Performance

Overall Score: {_score_badge(report.overall_score)}  
Hiring Probability: {_score_badge(report.hiring_probability)}

{gating_block}

---

## 📈 Percentile Ranking

{gaussian_img}

Percentile: {_score_badge(report.percentile_rank)}

{report.percentile_explanation}

---

## 🧭 Performance Overview

<div style="display:flex; gap:40px;">

<div style="flex:1;">
<h4>Dimension Breakdown</h4>
{radar_img}
</div>

<div style="flex:1;">
<h4>Highlights</h4>

<strong>Strongest Dimension:</strong><br>
{_badge(strongest.name, "#16a34a")}  
Score: {strongest.score}/100

<br><br>

<strong>Weakest Dimension:</strong><br>
{_badge(weakest.name, "#dc2626")}  
Score: {weakest.score}/100

<br><br>

<strong>Total Tokens Used:</strong> {report.total_tokens_used}

{_confidence_bar(report.confidence.final)}

</div>

</div>

---

## 📝 Question-Level Assessment

{question_block}

---

## 🚀 Improvement Roadmap

{improvements}

---

<small>
This evaluation combines deterministic scoring, role-weighted modeling, statistical percentile estimation, 
and AI-generated qualitative justification.
</small>
"""
