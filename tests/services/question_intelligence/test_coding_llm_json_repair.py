# tests/services/question_intelligence/test_coding_llm_json_repair.py

import json

import pytest

from services.question_intelligence.coding_llm_json_repair import repair_llm_json_text


def test_repair_python_tuples_to_json_arrays() -> None:

    raw = """
[
  {
    "prompt": "Find pairs.",
    "coding_spec": {
      "type": "function",
      "entrypoint": "find_pairs",
      "parameters": ["nums", "target"]
    },
    "visible_tests": [
      {
        "args": [[1, 2, 3], 6],
        "expected": [(1, 5), (2, 4)]
      }
    ]
  }
]
"""

    repaired = repair_llm_json_text(raw)
    data = json.loads(repaired)

    assert data[0]["visible_tests"][0]["expected"] == [[1, 5], [2, 4]]


def test_repair_fenced_json_block() -> None:

    payload = json.dumps(
        [
            {
                "prompt": "Return max of two ints. Implement max_of_two(a, b).",
                "coding_spec": {
                    "type": "function",
                    "entrypoint": "max_of_two",
                    "parameters": ["a", "b"],
                },
                "visible_tests": [
                    {"args": [1, 2], "expected": 2},
                ],
            },
        ],
    )

    raw = f"```json\n{payload}\n```"

    repaired = repair_llm_json_text(raw)

    assert json.loads(repaired) == json.loads(payload)


def test_repair_trailing_commas() -> None:

    raw = """
[
  {
    "prompt": "Example max_of_two(a, b).",
    "coding_spec": {
      "type": "function",
      "entrypoint": "max_of_two",
      "parameters": ["a", "b"],
    },
    "visible_tests": [
      {"args": [1, 2], "expected": 2,},
    ],
  },
]
"""

    repaired = repair_llm_json_text(raw)

    data = json.loads(repaired)

    assert data[0]["coding_spec"]["entrypoint"] == "max_of_two"


# ---------------------------------------------------------------------------
# R6.16 — field-aware repair regression tests
# ---------------------------------------------------------------------------

def _make_payload(reference_solution: str, args=None, expected=None) -> str:
    """Build a minimal valid LLM JSON response for use in tests."""
    return json.dumps(
        [
            {
                "prompt": "Implement solution().",
                "coding_spec": {
                    "type": "function",
                    "entrypoint": "solution",
                    "parameters": [],
                },
                "visible_tests": [
                    {
                        "args": args if args is not None else [],
                        "expected": expected if expected is not None else 0,
                    }
                ],
                "reference_solution": reference_solution,
            }
        ]
    )


@pytest.mark.parametrize(
    "code_snippet",
    [
        "def solution():\n    return globals().get('x', None)",
        "def solution():\n    seen = set()\n    return seen",
        "def solution():\n    from time import time\n    return time()",
        "def solution():\n    from collections import OrderedDict\n    return OrderedDict()",
        "def solution():\n    fn = lambda: None\n    return fn()",
        "def solution():\n    def helper():\n        pass\n    helper()\n    return 1",
    ],
    ids=[
        "globals()",
        "set()",
        "time()",
        "OrderedDict()",
        "lambda_call",
        "def_helper",
    ],
)
def test_reference_solution_is_not_mutated(code_snippet: str) -> None:
    """reference_solution must be byte-identical after repair."""
    payload = _make_payload(code_snippet)
    repaired = repair_llm_json_text(payload)
    data = json.loads(repaired)
    assert data[0]["reference_solution"] == code_snippet


def test_args_tuple_literals_are_normalised() -> None:
    """args containing Python-style tuple string values must be normalised."""
    # The LLM occasionally emits args as a string like "(1, 2)" instead of [1, 2].
    # When that string appears as the value of an "args" key it should be repaired.
    raw = json.dumps(
        [
            {
                "prompt": "Find pairs.",
                "coding_spec": {
                    "type": "function",
                    "entrypoint": "find_pairs",
                    "parameters": ["nums", "target"],
                },
                "visible_tests": [
                    {
                        "args": [[1, 2, 3], 6],
                        "expected": "(1, 5)",
                    }
                ],
                "reference_solution": "def find_pairs(nums, target): return []",
            }
        ]
    )
    repaired = repair_llm_json_text(raw)
    data = json.loads(repaired)
    assert data[0]["visible_tests"][0]["expected"] == [1, 5]


def test_expected_tuple_list_is_normalised() -> None:
    """The original test: expected=[(1,5),(2,4)] must still normalise to [[1,5],[2,4]]."""
    raw = """
[
  {
    "prompt": "Find pairs.",
    "coding_spec": {
      "type": "function",
      "entrypoint": "find_pairs",
      "parameters": ["nums", "target"]
    },
    "visible_tests": [
      {
        "args": [[1, 2, 3], 6],
        "expected": [(1, 5), (2, 4)]
      }
    ],
    "reference_solution": "def find_pairs(nums, target): return []"
  }
]
"""
    repaired = repair_llm_json_text(raw)
    data = json.loads(repaired)
    assert data[0]["visible_tests"][0]["expected"] == [[1, 5], [2, 4]]


def test_reference_solution_not_affected_when_expected_repaired() -> None:
    """Tuple repair on expected must not bleed into reference_solution."""
    ref = "def solution():\n    seen = set()\n    return seen"
    raw = """
[
  {
    "prompt": "Example.",
    "coding_spec": {"type": "function", "entrypoint": "solution", "parameters": []},
    "visible_tests": [{"args": [], "expected": (1, 2)}],
    "reference_solution": "def solution():\\n    seen = set()\\n    return seen"
  }
]
"""
    repaired = repair_llm_json_text(raw)
    data = json.loads(repaired)
    assert data[0]["reference_solution"] == ref
    assert data[0]["visible_tests"][0]["expected"] == [1, 2]


def test_prompt_field_is_not_mutated() -> None:
    """prompt field containing parentheses must not be altered."""
    prompt_text = "Implement solution(items) that returns set() of unique items."
    payload = json.dumps(
        [
            {
                "prompt": prompt_text,
                "coding_spec": {"type": "function", "entrypoint": "solution", "parameters": ["items"]},
                "visible_tests": [{"args": [[1, 1, 2]], "expected": 2}],
                "reference_solution": "def solution(items): return len(set(items))",
            }
        ]
    )
    repaired = repair_llm_json_text(payload)
    data = json.loads(repaired)
    assert data[0]["prompt"] == prompt_text
