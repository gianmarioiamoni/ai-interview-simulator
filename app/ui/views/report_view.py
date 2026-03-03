# app/ui/views/report_view.py


# =========================================================
# UI HELPERS
# =========================================================


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
    padding:6px 14px;
    border-radius:8px;
    font-weight:bold;
    font-size:16px;
">
{score}/100
</span>
"""


def _probability_badge(prob: float) -> str:
    if prob >= 70:
        color = "#16a34a"
    elif prob >= 40:
        color = "#ca8a04"
    else:
        color = "#dc2626"

    return f"""
<span style="
    background-color:{color};
    color:white;
    padding:6px 14px;
    border-radius:8px;
    font-weight:bold;
">
{prob}%
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
    <div style="margin-top:6px;font-size:14px;">
        {percentile}% percentile
    </div>
</div>
"""


def _confidence_bar(confidence: float) -> str:
    percent = round(confidence * 100, 1)

    if percent >= 80:
        color = "#16a34a"
    elif percent >= 60:
        color = "#ca8a04"
    else:
        color = "#dc2626"

    return f"""
<div style="margin-top:6px;">
    <div style="background:#e5e7eb;border-radius:6px;height:12px;">
        <div style="
            width:{percent}%;
            background:{color};
            height:12px;
            border-radius:6px;
        "></div>
    </div>
    <div style="margin-top:4px;font-size:13px;">
        Confidence: {percent}%
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
<div style="margin-bottom:16px;">
    <strong>{name}</strong>
    <div style="background:#e5e7eb;border-radius:6px;height:14px;margin-top:4px;">
        <div style="
            width:{score}%;
            background:{color};
            height:14px;
            border-radius:6px;
        "></div>
    </div>
    <div style="font-size:13px;margin-top:4px;">
        {score}/100
    </div>
</div>
"""


def _gating_block(triggered: bool, reason: str | None) -> str:

    if triggered:
        return f"""
<div style="
    background:#fee2e2;
    border:1px solid #dc2626;
    padding:12px;
    border-radius:8px;
    margin-top:12px;
">
<strong style="color:#dc2626;">🚨 Gating Triggered</strong><br>
{reason}
</div>
"""
    else:
        return """
<div style="
    background:#dcfce7;
    border:1px solid #16a34a;
    padding:12px;
    border-radius:8px;
    margin-top:12px;
">
<strong style="color:#16a34a;">✅ No Gating Applied</strong>
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

**Hiring Probability:** {_probability_badge(report.hiring_probability)}

---

## 📈 Percentile Ranking

{_percentile_bar(report.percentile_rank)}

{report.percentile_explanation}

---

## ⚖️ Gating Analysis

{_gating_block(report.gating_triggered, report.gating_reason)}

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

{_confidence_bar(report.confidence.final)}

---

*This evaluation combines deterministic scoring, weighted modeling, gating governance rules, and AI-generated qualitative justification.*
"""
