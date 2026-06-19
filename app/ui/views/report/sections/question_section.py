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
{hint_block}
{execution}
</div>
"""

    return f"<h2>Question-Level Assessment</h2>{html}"
