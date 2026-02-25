# tests/services/test_interview_evaluation_service_2.py

import json

from unittest.mock import Mock

from services.interview_evaluation_service import (
    InterviewEvaluationService,
)
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.performance_dimension import PerformanceDimension

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


def test_invalid_number_of_performance_dimensions_triggers_retry():
    llm = Mock()

    invalid_payload = valid_llm_payload()
    invalid_payload["performance_dimensions"] = invalid_payload[
        "performance_dimensions"
    ][:3]

    llm.invoke.side_effect = [
        Mock(content=json.dumps(invalid_payload)),
        Mock(content=json.dumps(valid_llm_payload())),
        Mock(content=json.dumps(valid_llm_payload())),
    ]

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.overall_score == 7.0


def test_duplicate_dimension_names_triggers_retry():
    llm = Mock()

    invalid_payload = valid_llm_payload()
    invalid_payload["performance_dimensions"][1]["name"] = invalid_payload[
        "performance_dimensions"
    ][0]["name"]

    llm.invoke.side_effect = [
        Mock(content=json.dumps(invalid_payload)),
        Mock(content=json.dumps(valid_llm_payload())),
        Mock(content=json.dumps(valid_llm_payload())),
    ]

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.overall_score == 7.0


def test_invalid_dimension_set_triggers_retry():
    llm = Mock()

    invalid_payload = valid_llm_payload()
    invalid_payload["performance_dimensions"][0]["name"] = "random_dimension"

    llm.invoke.side_effect = [
        Mock(content=json.dumps(invalid_payload)),
        Mock(content=json.dumps(valid_llm_payload())),
        Mock(content=json.dumps(valid_llm_payload())),
    ]

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.overall_score == 7.0


def test_overall_score_inconsistency_triggers_retry():
    llm = Mock()

    invalid_payload = valid_llm_payload()
    invalid_payload["overall_score"] = 1.0  # inconsistent

    llm.invoke.side_effect = [
        Mock(content=json.dumps(invalid_payload)),
        Mock(content=json.dumps(valid_llm_payload())),
        Mock(content=json.dumps(valid_llm_payload())),
    ]

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.overall_score == 7.0


def test_overall_score_bounded_between_1_and_10():
    llm = Mock()

    extreme_payload = valid_llm_payload()
    for d in extreme_payload["performance_dimensions"]:
        d["score"] = 20.0  # fuori range teorico

    llm.invoke.return_value = Mock(content=json.dumps(extreme_payload))

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert 1.0 <= result.overall_score <= 10.0


def test_confidence_decreases_with_high_variance():
    llm = Mock()

    payload = valid_llm_payload()
    scores = [1.0, 10.0, 1.0, 10.0]

    for i, d in enumerate(payload["performance_dimensions"]):
        d["score"] = scores[i]

    llm.invoke.return_value = Mock(content=json.dumps(payload))

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.confidence.base < 1.0
