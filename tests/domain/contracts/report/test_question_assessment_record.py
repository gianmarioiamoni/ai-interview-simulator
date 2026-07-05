# tests/domain/contracts/report/test_question_assessment_record.py
# EPIC-V13-01 Phase 8 — QuestionAssessmentRecord contract tests

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.contracts.report.question_assessment_record import QuestionAssessmentRecord


def _make_written() -> QuestionAssessmentRecord:
    return QuestionAssessmentRecord(
        question_id="q-001",
        question_index=0,
        question_type="written",
        area_label="Technical Coding",
        question_prompt="Explain Big-O notation.",
        score=75.0,
        max_score=100.0,
        feedback="Good explanation.",
        strengths=("Clear reasoning",),
        weaknesses=("Missing edge cases",),
        attempts=1,
    )


def _make_coding() -> QuestionAssessmentRecord:
    return QuestionAssessmentRecord(
        question_id="q-002",
        question_index=1,
        question_type="coding",
        area_label="Tech Coding",
        question_prompt="Implement binary search.",
        score=80.0,
        max_score=100.0,
        feedback="Correct implementation.",
        attempts=2,
        passed_tests=4,
        total_tests=5,
        execution_status="SUCCESS",
    )


class TestQuestionAssessmentRecordConstruction:
    def test_written_question_construction(self) -> None:
        rec = _make_written()
        assert rec.question_id == "q-001"
        assert rec.question_index == 0
        assert rec.question_type == "written"
        assert rec.score == 75.0
        assert rec.max_score == 100.0
        assert rec.schema_version == "1.0"

    def test_coding_question_construction(self) -> None:
        rec = _make_coding()
        assert rec.passed_tests == 4
        assert rec.total_tests == 5
        assert rec.execution_status == "SUCCESS"

    def test_is_frozen(self) -> None:
        rec = _make_written()
        with pytest.raises(ValidationError):
            rec.score = 99.0  # type: ignore[misc]

    def test_strengths_weaknesses_default_empty(self) -> None:
        rec = QuestionAssessmentRecord(
            question_id="q-x",
            question_index=0,
            question_type="written",
            area_label="HR",
            question_prompt="Tell me about yourself.",
            score=60.0,
            max_score=100.0,
            feedback="Decent answer.",
            attempts=1,
        )
        assert rec.strengths == ()
        assert rec.weaknesses == ()


class TestQuestionAssessmentRecordInvariants:
    def test_v_qrr_01_coding_pair_both_none_is_valid(self) -> None:
        rec = _make_written()
        assert rec.passed_tests is None
        assert rec.total_tests is None

    def test_v_qrr_01_coding_pair_both_set_is_valid(self) -> None:
        rec = _make_coding()
        assert rec.passed_tests is not None
        assert rec.total_tests is not None

    def test_v_qrr_01_only_passed_tests_raises(self) -> None:
        with pytest.raises(ValidationError):
            QuestionAssessmentRecord(
                question_id="q-x",
                question_index=0,
                question_type="coding",
                area_label="Tech",
                question_prompt="Prompt.",
                score=50.0,
                max_score=100.0,
                feedback="ok",
                attempts=1,
                passed_tests=2,
                total_tests=None,
            )

    def test_v_qrr_02_passed_tests_le_total_tests(self) -> None:
        with pytest.raises(ValidationError):
            QuestionAssessmentRecord(
                question_id="q-x",
                question_index=0,
                question_type="coding",
                area_label="Tech",
                question_prompt="Prompt.",
                score=50.0,
                max_score=100.0,
                feedback="ok",
                attempts=1,
                passed_tests=5,
                total_tests=3,
            )

    def test_v_qrr_03_hint_pair_suggestion_without_explanation_raises(self) -> None:
        with pytest.raises(ValidationError):
            QuestionAssessmentRecord(
                question_id="q-x",
                question_index=0,
                question_type="written",
                area_label="HR",
                question_prompt="Prompt.",
                score=50.0,
                max_score=100.0,
                feedback="ok",
                attempts=1,
                ai_hint_explanation=None,
                ai_hint_suggestion="Use a hash map.",
            )

    def test_v_qrr_03_hint_pair_both_set_is_valid(self) -> None:
        rec = QuestionAssessmentRecord(
            question_id="q-x",
            question_index=0,
            question_type="written",
            area_label="HR",
            question_prompt="Prompt.",
            score=50.0,
            max_score=100.0,
            feedback="ok",
            attempts=1,
            ai_hint_explanation="Think about the data structure.",
            ai_hint_suggestion="Use a hash map.",
        )
        assert rec.ai_hint_explanation is not None
        assert rec.ai_hint_suggestion is not None
