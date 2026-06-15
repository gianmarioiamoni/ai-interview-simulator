# tests/services/humanizer/test_humanizer_response_parser.py

import json
import pytest

from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.humanizer_response_parser import HumanizerResponseParser


def test_parse_valid_direct_question_response() -> None:

    parser = HumanizerResponseParser()

    payload = json.dumps({
        "decision": "direct_question",
        "message": "Tell me about your experience with distributed systems.",
    })

    result = parser.parse(payload)

    assert result.decision == HumanizerDecision.DIRECT_QUESTION
    assert result.message == "Tell me about your experience with distributed systems."


def test_parse_valid_follow_up_response() -> None:

    parser = HumanizerResponseParser()

    payload = json.dumps({
        "decision": "follow_up",
        "message": "That is a great point — can you go deeper on consistency?",
        "follow_up_used": True,
    })

    result = parser.parse(payload)

    assert result.decision == HumanizerDecision.FOLLOW_UP
    assert result.follow_up_used is True


def test_parse_valid_remark_plus_question_response() -> None:

    parser = HumanizerResponseParser()

    payload = json.dumps({
        "decision": "remark_plus_question",
        "message": "Good attempt. Now let's look at caching strategies.",
    })

    result = parser.parse(payload)

    assert result.decision == HumanizerDecision.REMARK_PLUS_QUESTION


def test_parse_response_with_score() -> None:

    parser = HumanizerResponseParser()

    payload = json.dumps({
        "decision": "direct_question",
        "message": "Next question.",
        "score": 7,
    })

    result = parser.parse(payload)

    assert result.score == 7


def test_parse_invalid_json_raises() -> None:

    parser = HumanizerResponseParser()

    with pytest.raises(Exception):
        parser.parse("not valid json")


def test_parse_missing_required_field_raises() -> None:

    parser = HumanizerResponseParser()

    # Missing required 'message' field
    payload = json.dumps({"decision": "direct_question"})

    with pytest.raises(Exception):
        parser.parse(payload)
