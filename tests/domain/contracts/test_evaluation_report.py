# tests/domain/contracts/test_evaluation_report.py

import pytest
from pydantic import ValidationError

from domain.contracts.evaluation_report import EvaluationReport
from domain.contracts.evaluation import EvaluationResult
from domain.contracts.confidence import Confidence


def _evaluation() -> EvaluationResult:
    return EvaluationResult(
        question_id="q1",
        score=80.0,
        max_score=100.0,
        feedback="Good",
        strengths=["Clarity"],
        weaknesses=["Depth"],
        passed=True,
    )


def test_evaluation_report_valid() -> None:
    report = EvaluationReport(
        interview_id="int-1",
        total_score=80.0,
        passed=True,
        feedback="Strong performance",
        evaluations=[_evaluation()],
        confidence=Confidence(base=0.8, final=0.85),
    )

    assert report.total_score == 80.0
    assert len(report.evaluations) == 1


def test_evaluation_report_without_evaluations_invalid() -> None:
    with pytest.raises(ValidationError):
        EvaluationReport(
            interview_id="int-1",
            total_score=80.0,
            passed=True,
            feedback="Invalid",
            evaluations=[],
            confidence=Confidence(base=0.8, final=0.85),
        )


def test_evaluation_report_invalid_score() -> None:
    with pytest.raises(ValidationError):
        EvaluationReport(
            interview_id="int-1",
            total_score=150.0,
            passed=True,
            feedback="Invalid",
            evaluations=[_evaluation()],
            confidence=Confidence(base=0.8, final=0.85),
        )


def test_evaluation_report_is_frozen() -> None:
    report = EvaluationReport(
        interview_id="int-1",
        total_score=80.0,
        passed=True,
        feedback="Strong performance",
        evaluations=[_evaluation()],
        confidence=Confidence(base=0.8, final=0.85),
    )

    with pytest.raises(ValidationError):
        report.total_score = 90.0
