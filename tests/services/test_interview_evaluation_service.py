# Tests for InterviewEvaluationService
#
# Responsibility:
# - verify strict JSON parsing
# - verify retry logic
# - verify mathematical consistency enforcement
# - verify deterministic normalization

import pytest
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

  
    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )
    # Should fallback after retries
    assert result.confidence == 0.3
    assert result.improvement_suggestions == ["Manual review recommended"]


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

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    # Should fallback after retries
    assert result.confidence == 0.3
    assert result.improvement_suggestions == ["Manual review recommended"]
    assert llm.invoke.call_count == 3


def test_retry_when_extra_field_in_root():

    llm = Mock()

    invalid_payload = {
        "overall_score": 7.0,
        "performance_dimensions": [
            {"name": "Technical Depth", "score": 7, "justification": "Solid"},
            {"name": "Communication", "score": 7, "justification": "Clear"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": 0.9,
        "unexpected_field": "hallucination",  # <-- extra
    }

    llm.invoke.return_value.content = __import__("json").dumps(invalid_payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    # Should fallback after retries
    assert result.confidence == 0.3
    assert result.improvement_suggestions == ["Manual review recommended"]


def test_retry_when_extra_field_in_dimension():

    llm = Mock()

    invalid_payload = {
        "overall_score": 7.0,
        "performance_dimensions": [
            {
                "name": "Technical Depth",
                "score": 7,
                "justification": "Solid",
                "extra": "invalid",  # <-- extra
            },
            {"name": "Communication", "score": 7, "justification": "Clear"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": 0.9,
    }

    llm.invoke.return_value.content = __import__("json").dumps(invalid_payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.confidence == 0.3


def test_retry_when_required_field_missing():

    llm = Mock()

    invalid_payload = {
        # missing overall_score
        "performance_dimensions": [
            {"name": "Technical Depth", "score": 7, "justification": "Solid"},
            {"name": "Communication", "score": 7, "justification": "Clear"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": 0.9,
    }

    llm.invoke.return_value.content = __import__("json").dumps(invalid_payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        per_question_evaluations=build_question_evaluations(),
        interview_type="technical",
        role="backend engineer",
    )

    assert result.confidence == 0.3


def test_invalid_dimension_count_triggers_fallback():

    llm = Mock()

    invalid_payload = {
        "overall_score": 7.0,
        "performance_dimensions": [  # only 3
            {"name": "Technical Depth", "score": 7, "justification": "Solid"},
            {"name": "Communication", "score": 7, "justification": "Clear"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": 0.8,
    }

    llm.invoke.return_value.content = json.dumps(invalid_payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.confidence == 0.3


def test_duplicate_dimension_names_triggers_fallback():

    llm = Mock()

    invalid_payload = {
        "overall_score": 7.0,
        "performance_dimensions": [
            {"name": "Technical Depth", "score": 7, "justification": "Solid"},
            {"name": "Technical Depth", "score": 7, "justification": "Duplicate"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": 0.8,
    }

    llm.invoke.return_value.content = json.dumps(invalid_payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.confidence == 0.3


def test_invalid_dimension_set_triggers_fallback():

    llm = Mock()

    invalid_payload = {
        "overall_score": 7.0,
        "performance_dimensions": [
            {"name": "Leadership", "score": 7, "justification": "Invalid"},
            {"name": "Communication", "score": 7, "justification": "Clear"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": 0.8,
    }

    llm.invoke.return_value.content = json.dumps(invalid_payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.confidence == 0.3


def test_invalid_confidence_triggers_fallback():

    llm = Mock()

    invalid_payload = {
        "overall_score": 7.0,
        "performance_dimensions": [
            {"name": "Technical Depth", "score": 7, "justification": "Solid"},
            {"name": "Communication", "score": 7, "justification": "Clear"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": 5.0,  # invalid
    }

    llm.invoke.return_value.content = json.dumps(invalid_payload)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.confidence == 0.3


def test_confidence_with_single_dimension():

    service = InterviewEvaluationService(Mock())

    dimensions = [
        PerformanceDimension(name="Technical Depth", score=7, justification="Only one")
    ]

    confidence = service._compute_confidence(dimensions)

    assert confidence == 0.5


def test_invalid_confidence_value_branch():

    llm = Mock()

    valid_except_confidence = {
        "overall_score": 7.0,
        "performance_dimensions": [
            {"name": "Technical Depth", "score": 7, "justification": "Solid"},
            {"name": "Communication", "score": 7, "justification": "Clear"},
            {"name": "Problem Solving", "score": 7, "justification": "Good"},
            {"name": "System Design", "score": 7, "justification": "Good"},
        ],
        "hiring_probability": 70,
        "per_question_assessment": [],
        "improvement_suggestions": [],
        "confidence": -1.0,  # invalid but passes JSON validation
    }

    llm.invoke.return_value.content = json.dumps(valid_except_confidence)

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.confidence == 0.3


def test_fallback_with_no_question_evaluations():

    service = InterviewEvaluationService(Mock())

    result = service._fallback_evaluation([])

    assert result.overall_score == 5.0
    assert result.confidence == 0.3


def test_guard_final_fallback_branch(monkeypatch):

    service = InterviewEvaluationService(Mock())

    monkeypatch.setattr(
        "services.interview_evaluation_service.MAX_RETRIES",
        -1,
    )

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.confidence == 0.3


def test_json_with_prefix_text():

    llm = Mock()

    payload = valid_llm_payload()

    dirty_response = f"""
    Sure! Here is your evaluation:

    {json.dumps(payload)}

    Let me know if you need more details.
    """

    llm.invoke.return_value.content = dirty_response

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.overall_score == 7.0


def test_json_with_suffix_text():

    llm = Mock()

    payload = valid_llm_payload()

    dirty_response = json.dumps(payload) + "\n\nThanks!"

    llm.invoke.return_value.content = dirty_response

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.overall_score == 7.0


def test_no_json_triggers_fallback():

    llm = Mock()
    llm.invoke.return_value.content = "Completely invalid output"

    service = InterviewEvaluationService(llm)

    result = service.evaluate(
        build_question_evaluations(),
        "technical",
        "backend engineer",
    )

    assert result.confidence == 0.3

