# Tests for InterviewEvaluationService
#
# Responsibility:
# - verify strict JSON parsing
# - verify retry logic
# - verify mathematical consistency enforcement
# - verify deterministic normalization

import pytest
from unittest.mock import Mock

from services.interview_evaluation_service import (
    InterviewEvaluationService,
)
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.interview_evaluation import InterviewEvaluation

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def build_question_evaluations():

    return [
        QuestionEvaluation(
            question_id="q1",
            score=80,
            max_score=100,
            feedback="Good answer",
            strengths=["clarity"],
            weaknesses=["depth"],
            passed=True,
        ),
        QuestionEvaluation(
            question_id="q2",
            score=60,
            max_score=100,
            feedback="Average answer",
            strengths=["structure"],
            weaknesses=["accuracy"],
            passed=True,
        ),
    ]


def valid_llm_payload():

    return {
        "overall_score": 7.0,
        "performance_dimensions": [
            {"name": "Technical Depth", "score": 7, "justification": "Solid"},
            {"name": "Communication", "score": 8, "justification": "Clear"},
            {"name": "Problem Solving", "score": 6, "justification": "Decent"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 75,
        "per_question_assessment": [],
        "improvement_suggestions": ["Improve depth"],
        "confidence": 0.9,
    }


# ------------------------------------------------------------------
# Happy Path
# ------------------------------------------------------------------


def test_evaluation_success():

    llm = Mock()

    payload = valid_llm_payload()
    llm.invoke.return_value.content = __import__("json").dumps(payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert isinstance(result, InterviewEvaluation)
    assert result.overall_score == 7.0
    assert result.hiring_probability == 70.0
    assert len(result.performance_dimensions) == 4


# ------------------------------------------------------------------
# Retry on malformed JSON
# ------------------------------------------------------------------


def test_retry_on_invalid_json():

    llm = Mock()

    llm.invoke.side_effect = [
        Mock(content="INVALID_JSON"),
        Mock(content=__import__("json").dumps(valid_llm_payload())),
    ]

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.overall_score == 7.0
    assert llm.invoke.call_count == 2


# ------------------------------------------------------------------
# Inconsistent overall score triggers retry
# ------------------------------------------------------------------


def test_retry_on_inconsistent_score():

    llm = Mock()

    inconsistent_payload = valid_llm_payload()
    inconsistent_payload["overall_score"] = 2.0

    llm.invoke.side_effect = [
        Mock(content=__import__("json").dumps(inconsistent_payload)),
        Mock(content=__import__("json").dumps(valid_llm_payload())),
    ]

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.overall_score == 7.0
    assert llm.invoke.call_count == 2


# ------------------------------------------------------------------
# Fail after max retries
# ------------------------------------------------------------------


def test_fail_after_max_retries():

    llm = Mock()
    llm.invoke.return_value.content = "INVALID_JSON"

    service = InterviewEvaluationService(llm)

    with pytest.raises(Exception):
        service.evaluate(
            per_question_evaluations=build_question_evaluations(),
            interview_type="technical",
            role="backend engineer",
        )


def test_fail_after_inconsistent_score_retries():

    llm = Mock()

    inconsistent_payload = {
        "overall_score": 1.0,
        "performance_dimensions": [
            {"name": "Technical Depth", "score": 8, "justification": "Solid"},
            {"name": "Communication", "score": 8, "justification": "Clear"},
            {"name": "Problem Solving", "score": 8, "justification": "Good"},
            {"name": "System Design", "score": 8, "justification": "Good"},
        ],
        "hiring_probability": 10,
        "per_question_assessment": [],
        "improvement_suggestions": ["Improve"],
        "confidence": 0.8,
    }

    llm.invoke.return_value.content = __import__("json").dumps(inconsistent_payload)

    service = InterviewEvaluationService(llm)

    with pytest.raises(Exception):
        service.evaluate(
            per_question_evaluations=build_question_evaluations(),
            interview_type="technical",
            role="backend engineer",
        )

    # Should attempt MAX_RETRIES + 1 times
    assert llm.invoke.call_count == 3
