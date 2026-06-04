# tests/services/question_intelligence/test_coding_llm_json_repair.py

import json

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
