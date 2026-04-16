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

        html += f"""
<div style="border:1px solid #ddd;padding:10px;margin-bottom:10px;border-radius:8px;">
<strong>Question {q.question_id}</strong><br>
Score: {score_badge(q.score)}<br><br>
{q.feedback}
{execution}
</div>
"""

    return f"<h2>Question-Level Assessment</h2>{html}"
