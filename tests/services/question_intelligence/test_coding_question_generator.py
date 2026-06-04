# tests/services/question_intelligence/test_coding_question_generator.py

import json
from unittest.mock import MagicMock

import pytest

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
    MAX_INVALID_JSON_ATTEMPTS,
)

VALID_CODING_JSON = json.dumps(
    [
        {
            "prompt": (
                "Return the larger of two integers a and b. "
                "Implement max_of_two(a, b)."
            ),
            "coding_spec": {
                "type": "function",
                "entrypoint": "max_of_two",
                "parameters": ["a", "b"],
            },
            "visible_tests": [
                {"args": [1, 2], "expected": 2},
                {"args": [5, 3], "expected": 5},
            ],
        },
    ],
)

TUPLE_BROKEN_JSON = """
[
  {
    "prompt": "Find pairs with find_pairs(nums, target).",
    "coding_spec": {
      "type": "function",
      "entrypoint": "find_pairs",
      "parameters": ["nums", "target"]
    },
    "visible_tests": [
      {
        "args": [[1, 2, 3], 6],
        "expected": [(1, 5), (2, 4)]
      },
      {
        "args": [[-1, 0, 1], 3],
        "expected": [(-1, 2), (0, 3)]
      }
    ]
  }
]
"""

INVALID_JSON = "not-json-at-all"

VALIDATION_FAILURE_JSON = json.dumps(
    [
        {
            "prompt": "Missing spec",
            "visible_tests": [{"args": [1], "expected": 1}],
        },
    ],
)


def _mock_llm_with_responses(responses: list[str]) -> MagicMock:

    llm = MagicMock()
    llm.invoke.side_effect = [
        MagicMock(content=content) for content in responses
    ]

    return llm


def test_parse_tuple_payload_after_repair() -> None:

    llm = _mock_llm_with_responses([TUPLE_BROKEN_JSON])
    generator = CodingQuestionGenerator(llm)

    result = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
        n=1,
    )

    assert len(result) == 1
    assert result[0].coding_spec.entrypoint == "find_pairs"
    llm.invoke.assert_called_once()


def test_parse_fenced_json_after_repair() -> None:

    fenced = f"```json\n{VALID_CODING_JSON}\n```"
    llm = _mock_llm_with_responses([fenced])
    generator = CodingQuestionGenerator(llm)

    result = generator.generate(
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.MID,
        n=1,
    )

    assert len(result) == 1
    assert result[0].coding_spec.entrypoint == "max_of_two"


def test_invalid_json_retry_success() -> None:

    llm = _mock_llm_with_responses([INVALID_JSON, VALID_CODING_JSON])
    generator = CodingQuestionGenerator(llm)

    result = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
        n=1,
    )

    assert len(result) == 1
    assert llm.invoke.call_count == 2


def test_invalid_json_retry_exhausted_returns_empty() -> None:

    llm = _mock_llm_with_responses(
        [INVALID_JSON] * MAX_INVALID_JSON_ATTEMPTS,
    )
    generator = CodingQuestionGenerator(llm)

    result = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
        n=1,
    )

    assert result == []
    assert llm.invoke.call_count == MAX_INVALID_JSON_ATTEMPTS


def test_generate_never_propagates_value_error() -> None:

    llm = _mock_llm_with_responses([VALIDATION_FAILURE_JSON] * 2)
    generator = CodingQuestionGenerator(llm)

    try:
        result = generator.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            n=1,
        )
    except ValueError:
        pytest.fail("generate() must not propagate ValueError")

    assert result == []


def test_validation_failure_does_not_retry() -> None:

    llm = _mock_llm_with_responses([VALIDATION_FAILURE_JSON])
    generator = CodingQuestionGenerator(llm)

    result = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        n=1,
    )

    assert result == []
    llm.invoke.assert_called_once()


def test_enrich_from_prompt_returns_none_on_exhausted_invalid_json() -> None:

    llm = _mock_llm_with_responses([INVALID_JSON] * MAX_INVALID_JSON_ATTEMPTS)
    generator = CodingQuestionGenerator(llm)

    enriched = generator.enrich_from_prompt(
        seed_prompt="How would you solve Two Sum?",
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.JUNIOR,
    )

    assert enriched is None
