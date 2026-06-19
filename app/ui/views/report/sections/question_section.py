# app/ui/views/report/sections/question_section.py

from app.ui.views.report.components.badges import score_badge, badge
from app.ui.views.report.components.bars import test_progress_bar


def render_questions(report):

    html = ""

    for q in report.question_assessments:

        execution = ""

        if q.passed_tests is not None:
            execution += test_progress_bar(q.passed_tests, q.total_tests)

        if q.execution_status:
            color = "#16a34a" if q.execution_status == "success" else "#dc2626"
            execution += f"<br>{badge(q.execution_status.upper(), color)}"

        strengths_block = ""
        if q.strengths:
            items = "".join(f"<li>{s}</li>" for s in q.strengths)
            strengths_block = f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:6px;padding:8px 12px;margin-top:10px;">
<strong>✅ Strengths</strong>
<ul style="margin:6px 0 0 0;padding-left:18px;">{items}</ul>
</div>"""

        weaknesses_block = ""
        if q.weaknesses:
            items = "".join(f"<li>{w}</li>" for w in q.weaknesses)
            weaknesses_block = f"""
<div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:6px;padding:8px 12px;margin-top:10px;">
<strong>⚠️ Areas to Improve</strong>
<ul style="margin:6px 0 0 0;padding-left:18px;">{items}</ul>
</div>"""

        follow_up_block = ""
        if q.follow_up_question:
            follow_up_block = f"""
<div style="background:#eff6ff;border:1px solid #93c5fd;border-radius:6px;padding:8px 12px;margin-top:10px;">
<strong>🔍 Suggested Interviewer Follow-Up</strong>
<p style="margin:6px 0 0 0;font-style:italic;">{q.follow_up_question}</p>
</div>"""

        hint_block = ""
        if q.ai_hint_explanation:
            suggestion_line = (
                f"<p style='margin:4px 0 0 0;'><strong>Suggestion:</strong> {q.ai_hint_suggestion}</p>"
                if q.ai_hint_suggestion
                else ""
            )
            hint_block = f"""
<div style="background:#fefce8;border:1px solid #fde047;border-radius:6px;padding:8px 12px;margin-top:10px;">
<strong>💡 AI Coaching Hint</strong>
<p style="margin:6px 0 0 0;"><strong>Explanation:</strong> {q.ai_hint_explanation}</p>
{suggestion_line}
</div>"""

        html += f"""
<div style="border:1px solid #ddd;padding:10px;margin-bottom:10px;border-radius:8px;">
<strong>Question {q.question_id}</strong><br>
Score: {score_badge(q.score)}<br><br>
{q.feedback}
{strengths_block}
{weaknesses_block}
{follow_up_block}
{hint_block}
{execution}
</div>
"""

    return f"<h2>Question-Level Assessment</h2>{html}"
