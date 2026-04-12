# services/question_intelligence/coding_question_generator.py

import json
from typing import List

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.execution.coding_spec import CodingSpec
from infrastructure.llm.llm_factory import get_llm


# =========================================================
# DTOs (Structured Output)
# =========================================================

class GeneratedTestCase(BaseModel):
    args: List = Field(default_factory=list)
    expected: object

class GeneratedCodingQuestion(BaseModel):
    prompt: str
    coding_spec: CodingSpec
    visible_tests: List[GeneratedTestCase]


# =========================================================
# Generator
# =========================================================

class CodingQuestionGenerator:

    def __init__(self) -> None:
        self._llm = get_llm()

    def generate(
        self,
        role: str,
        level: str,
        n: int = 1,
    ) -> List[GeneratedCodingQuestion]:

        prompt = self._build_prompt(role, level, n)

        response = self._llm.invoke(prompt)

        try:
            raw_data = json.loads(response.content)
        except Exception as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")

        validated_items: List[GeneratedCodingQuestion] = []

        for item in raw_data:
            try:
                validated = GeneratedCodingQuestion.model_validate(item)
                validated_items.append(validated)
            except ValidationError as e:
                raise ValueError(f"Invalid coding question structure: {e}")

        return validated_items

    # =========================================================
    # PROMPT
    # =========================================================

    def _build_prompt(
        self,
        role: str,
        level: str,
        n: int,
    ) -> str:

        return f"""
You are a senior technical interviewer.

Generate {n} Python coding interview questions for a {level} {role}.

Each question MUST include:

1. A clear problem description
2. A strict function contract
3. Valid test cases

Return STRICT JSON array:

[
  {{
    "prompt": "...",

    "coding_spec": {{
      "type": "function",
      "entrypoint": "function_name",
      "parameters": ["param1", "param2"]
    }},

    "visible_tests": [
      {{
        "args": [...],
        "expected": ...
      }}
    ]
  }}
]

Rules:
- Function name MUST match coding_spec.entrypoint
- Parameters MUST match coding_spec.parameters
- The function signature MUST be clearly described in the prompt
- Avoid ambiguous descriptions
- No markdown
- Only valid JSON
"""
