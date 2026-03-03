# app/ui/views/report_view.py


def _score_badge(score: float) -> str:
    if score >= 80:
        color = "#16a34a"  # green
    elif score >= 60:
        color = "#ca8a04"  # amber
    else:
        color = "#dc2626"  # red

    return f"""
<span style="
    background-color:{color};
    color:white;
    padding:6px 12px;
    border-radius:8px;
    font-weight:bold;
    font-size:16px;
">
{score}/100
</span>
"""


def _percentile_bar(percentile: float) -> str:
    return f"""
<div style="margin-top:8px;">
    <div style="background:#e5e7eb;border-radius:6px;height:16px;">
        <div style="
            width:{percentile}%;
            background:#2563eb;
            height:16px;
            border-radius:6px;
        "></div>
    </div>
    <div style="margin-top:4px;font-size:14px;">
        {percentile}% percentile
    </div>
</div>
"""


def _dimension_bar(name: str, score: float) -> str:

    if score >= 75:
        color = "#16a34a"
    elif score >= 50:
        color = "#ca8a04"
    else:
        color = "#dc2626"

    return f"""
<div style="margin-bottom:14px;">
    <strong>{name}</strong>
    <div style="background:#e5e7eb;border-radius:6px;height:14px;margin-top:4px;">
        <div style="
            width:{score}%;
            background:{color};
            height:14px;
            border-radius:6px;
        "></div>
    </div>
    <div style="font-size:13px;margin-top:2px;">
        {score}/100
    </div>
</div>
"""


# =========================================================
# PUBLIC REPORT RENDER
# =========================================================


def build_report_markdown(report) -> str:

    # ---------------------------------------------------------
    # Dimension Breakdown
    # ---------------------------------------------------------

    dimension_block = ""
    for dim in report.dimension_scores:
        dimension_block += _dimension_bar(dim.name, dim.score)

    # ---------------------------------------------------------
    # Question Assessment
    # ---------------------------------------------------------

    question_block = ""
    for q in report.question_assessments:
        question_block += f"""
### Question {q.question_id}

**Score:** {_score_badge(q.score)}

**Feedback:**  
{q.feedback}
"""

    # ---------------------------------------------------------
    # Improvements
    # ---------------------------------------------------------

    improvement_block = ""
    for imp in report.improvement_suggestions:
        improvement_block += f"- {imp}\n"

    # ---------------------------------------------------------
    # Final Markdown
    # ---------------------------------------------------------

    return f"""
# 🧠 AI Interview Final Evaluation

---

## 📊 Executive Summary

{report.executive_summary}

---

## 🎯 Overall Performance

**Overall Score:** {_score_badge(report.overall_score)}

**Hiring Probability:** {report.hiring_probability}%  

## 📈 Percentile Ranking

{_percentile_bar(report.percentile_rank)}

{report.percentile_explanation}

---

## ⚖️ Weighted Contribution

{"".join([f"<div>{k}: {v}</div>" for k, v in report.weighted_breakdown.items()])}

---

## 📊 Performance Breakdown

{dimension_block}

---

## 📝 Question-Level Assessment

{question_block}

---

## 🚀 Improvement Roadmap

{improvement_block}

---

## 🔎 Technical Appendix

**Total Tokens Used:** {report.total_tokens_used}

Confidence (Final): {report.confidence.final}

---

*This evaluation combines deterministic scoring, weighted modeling, gating governance rules, and AI-generated qualitative justification.*
"""
