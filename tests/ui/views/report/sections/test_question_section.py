# tests/ui/views/report/sections/test_question_section.py

import types

import pytest

from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO
from app.ui.views.report.sections.question_section import render_questions


def _make_report(*assessments: QuestionAssessmentDTO):
    report = types.SimpleNamespace()
    report.question_assessments = list(assessments)
    return report


def _base_assessment(**kwargs) -> QuestionAssessmentDTO:
    defaults = dict(
        question_id="q1",
        area="Coding",
        score=75.0,
        feedback="Good attempt.",
        passed_tests=None,
        total_tests=None,
        execution_status=None,
        strengths=[],
        weaknesses=[],
        follow_up_question=None,
    )
    defaults.update(kwargs)
    return QuestionAssessmentDTO(**defaults)


# ------------------------------------------------------------------
# Hint block rendering
# ------------------------------------------------------------------


def test_hint_block_rendered_when_explanation_present():
    assessment = _base_assessment(
        ai_hint_explanation="Check your loop boundary conditions.",
        ai_hint_suggestion="Move the return statement outside the inner loop.",
    )
    html = render_questions(_make_report(assessment))

    assert "AI Coaching Hint" in html
    assert "Check your loop boundary conditions." in html
    assert "Move the return statement outside the inner loop." in html


def test_hint_block_omitted_when_explanation_is_none():
    assessment = _base_assessment(ai_hint_explanation=None, ai_hint_suggestion=None)
    html = render_questions(_make_report(assessment))

    assert "AI Coaching Hint" not in html


def test_hint_block_omitted_when_fields_not_set():
    assessment = _base_assessment()
    html = render_questions(_make_report(assessment))

    assert "AI Coaching Hint" not in html


def test_hint_suggestion_omitted_gracefully_when_only_explanation_present():
    assessment = _base_assessment(
        ai_hint_explanation="Check your loop boundary conditions.",
        ai_hint_suggestion=None,
    )
    html = render_questions(_make_report(assessment))

    assert "AI Coaching Hint" in html
    assert "Check your loop boundary conditions." in html
    assert "Suggestion:" not in html


# ------------------------------------------------------------------
# Existing feedback rendering unchanged
# ------------------------------------------------------------------


def test_feedback_always_rendered():
    assessment = _base_assessment(feedback="Well structured solution.")
    html = render_questions(_make_report(assessment))

    assert "Well structured solution." in html


def test_question_id_always_rendered():
    assessment = _base_assessment(question_id="q42")
    html = render_questions(_make_report(assessment))

    assert "Question q42" in html


def test_score_always_rendered():
    assessment = _base_assessment(score=88.0)
    html = render_questions(_make_report(assessment))

    assert "88" in html


# ------------------------------------------------------------------
# Execution block rendering unchanged
# ------------------------------------------------------------------


def test_execution_progress_bar_rendered_when_tests_present():
    assessment = _base_assessment(passed_tests=3, total_tests=5)
    html = render_questions(_make_report(assessment))

    assert "3" in html
    assert "5" in html


def test_execution_status_badge_rendered_when_present():
    assessment = _base_assessment(execution_status="success")
    html = render_questions(_make_report(assessment))

    assert "SUCCESS" in html


def test_execution_block_absent_when_no_tests_or_status():
    assessment = _base_assessment()
    html = render_questions(_make_report(assessment))

    assert "tests passed" not in html


# ------------------------------------------------------------------
# Strengths block rendering
# ------------------------------------------------------------------


def test_strengths_block_rendered_when_present():
    assessment = _base_assessment(strengths=["Clear explanation", "Correct terminology"])
    html = render_questions(_make_report(assessment))

    assert "Strengths" in html
    assert "Clear explanation" in html
    assert "Correct terminology" in html


def test_weaknesses_block_rendered_when_present():
    assessment = _base_assessment(weaknesses=["Missing edge cases", "Shallow on complexity"])
    html = render_questions(_make_report(assessment))

    assert "Areas to Improve" in html
    assert "Missing edge cases" in html
    assert "Shallow on complexity" in html


def test_both_strengths_and_weaknesses_rendered():
    assessment = _base_assessment(
        strengths=["Good structure"],
        weaknesses=["Needs more depth"],
    )
    html = render_questions(_make_report(assessment))

    assert "Strengths" in html
    assert "Good structure" in html
    assert "Areas to Improve" in html
    assert "Needs more depth" in html


def test_strengths_block_absent_when_empty_list():
    assessment = _base_assessment(strengths=[])
    html = render_questions(_make_report(assessment))

    assert "Strengths" not in html


def test_weaknesses_block_absent_when_empty_list():
    assessment = _base_assessment(weaknesses=[])
    html = render_questions(_make_report(assessment))

    assert "Areas to Improve" not in html


def test_strengths_weaknesses_appear_before_hint_block():
    assessment = _base_assessment(
        strengths=["Good"],
        weaknesses=["Needs work"],
        ai_hint_explanation="Check boundaries.",
        ai_hint_suggestion="Fix the loop.",
    )
    html = render_questions(_make_report(assessment))

    strengths_pos = html.index("Strengths")
    weaknesses_pos = html.index("Areas to Improve")
    hint_pos = html.index("AI Coaching Hint")

    assert strengths_pos < hint_pos
    assert weaknesses_pos < hint_pos


# ------------------------------------------------------------------
# Follow-up question block rendering
# ------------------------------------------------------------------


def test_follow_up_block_rendered_when_present():
    assessment = _base_assessment(
        follow_up_question="Can you clarify what you mean by eventual consistency?"
    )
    html = render_questions(_make_report(assessment))

    assert "Suggested Interviewer Follow-Up" in html
    assert "Can you clarify what you mean by eventual consistency?" in html


def test_follow_up_block_absent_when_none():
    assessment = _base_assessment(follow_up_question=None)
    html = render_questions(_make_report(assessment))

    assert "Suggested Interviewer Follow-Up" not in html


def test_follow_up_appears_before_hint_block():
    assessment = _base_assessment(
        follow_up_question="Can you elaborate on caching?",
        ai_hint_explanation="Check boundaries.",
        ai_hint_suggestion="Fix the loop.",
    )
    html = render_questions(_make_report(assessment))

    follow_up_pos = html.index("Suggested Interviewer Follow-Up")
    hint_pos = html.index("AI Coaching Hint")

    assert follow_up_pos < hint_pos


def test_follow_up_and_hint_coexist_independently():
    assessment = _base_assessment(
        follow_up_question="How would you handle cache invalidation at scale?",
        ai_hint_explanation="Revisit your approach.",
        ai_hint_suggestion="Check edge cases.",
    )
    html = render_questions(_make_report(assessment))

    assert "Suggested Interviewer Follow-Up" in html
    assert "AI Coaching Hint" in html
    assert html.count("Suggested Interviewer Follow-Up") == 1
    assert html.count("AI Coaching Hint") == 1


# ------------------------------------------------------------------
# Multiple questions
# ------------------------------------------------------------------


def test_multiple_questions_rendered_independently():
    a1 = _base_assessment(question_id="q1", ai_hint_explanation="Hint for q1.", ai_hint_suggestion="Fix q1.")
    a2 = _base_assessment(question_id="q2", ai_hint_explanation=None, ai_hint_suggestion=None)
    html = render_questions(_make_report(a1, a2))

    assert html.count("AI Coaching Hint") == 1
    assert "Question q1" in html
    assert "Question q2" in html
