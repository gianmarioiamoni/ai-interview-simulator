# app/ui/views/report_view.py


def build_report_markdown(report, state) -> str:

    confidence_value = state.final_evaluation.confidence.final

    # ---------------------------------------------------------
    # Performance breakdown
    # ---------------------------------------------------------

    dimension_block = ""
    for dim in report.dimension_scores:
        dimension_block += f"- **{dim.name}**: {round(dim.score,1)}/100\n"

    # ---------------------------------------------------------
    # Question-level assessment
    # ---------------------------------------------------------

    question_block = ""
    for q in report.question_assessments:
        question_block += (
            f"\n### Question {q.question_id}\n"
            f"- Score: {round(q.score,1)}/100\n"
            f"- Feedback: {q.feedback}\n"
        )

    # ---------------------------------------------------------
    # Improvements
    # ---------------------------------------------------------

    improvement_block = ""
    for imp in report.improvement_suggestions:
        improvement_block += f"- {imp}\n"

    # ---------------------------------------------------------
    # Final Markdown
    # ---------------------------------------------------------

    report_text = f"""
# 🧠 AI Interview Final Evaluation

---

## 📊 Executive Summary

{report.executive_summary}

---

## 🎯 Overall Metrics

- **Overall Score:** {report.overall_score}/100  
- **Hiring Probability:** {report.hiring_probability}%  
- **Percentile Rank:** {report.percentile_rank}%  

---

## ⚖️ Decision Logic

### Weighted Contribution

{chr(10).join([f"- {k}: {v}" for k,v in report.weighted_breakdown.items()])}

### Gating Analysis

{"🚨 Gating triggered." if report.gating_triggered else "✅ No gating applied."}

{report.gating_reason if report.gating_reason else ""}

---

## 📈 Performance Breakdown

{dimension_block}

---

## 📝 Question-Level Assessment

{question_block}

---

## 🚀 Improvement Roadmap

{improvement_block}

---

## 🔎 Technical Appendix

### Confidence Model

Stability Index: {confidence_value}

Confidence derived from variance across dimension scores.
Higher variance → lower stability → lower confidence.
Formula:
Confidence = 1 − (Variance / 2500)

where 2500 represents the maximum theoretical variance 
on a 0–100 scoring scale.

### Confidence Interpretation Guide

Confidence ranges between 0 and 1 and reflects score stability 
based on normalized variance.

- 0.80 – 1.00 → Highly consistent performance across dimensions  
- 0.60 – 0.79 → Moderately consistent performance  
- 0.40 – 0.59 → Noticeable variability  
- 0.20 – 0.39 → Highly inconsistent performance  
- 0.00 – 0.19 → Extreme volatility in results  

### Percentile Methodology

{report.percentile_explanation}

---

*This evaluation combines deterministic scoring, weighted role-based modeling, gating governance rules, and AI-generated qualitative justification.*
"""

    return report_text
