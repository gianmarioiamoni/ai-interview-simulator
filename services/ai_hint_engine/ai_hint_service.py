# services/ai_hint_engine/ai_hint_service.py

import json
from typing import Optional
from domain.contracts.ai.ai_hint import AIHintInput, AIHint
from infrastructure.llm.llm_factory import get_llm


class AIHintService:

    def __init__(self):
        self._llm = get_llm()

    def generate_hint(
        self,
        input_data: AIHintInput,
        level: Optional[str] = None,
    ) -> AIHint:

        effective_level = level or input_data.hint_level.value
        prompt = self._build_prompt(input_data, effective_level)

        try:
            response = self._llm.invoke(prompt)
            content = response.content.strip()
            return self._parse_response(content)

        except Exception:
            return self._fallback_hint(effective_level)

    def _build_prompt(self, input_data: AIHintInput, level: str) -> str:

        level_instruction = self._get_level_instruction(level)

        return f"""
You are a senior Python interviewer helping a candidate debug their solution.

HINT LEVEL:
{level}

INSTRUCTIONS:
{level_instruction}

QUESTION:
{input_data.question}

USER CODE:
{input_data.user_code}

ERROR:
{input_data.error}

FAILED TESTS:
{input_data.failed_tests}

RULES:
- Be concise
- No hallucinations
- JSON only

FORMAT:
{{
  "explanation": "...",
  "suggestion": "..."
}}
"""

    def _get_level_instruction(self, level: str) -> str:

        if level == "BASIC":
            return "High-level hint. No code."

        if level == "TARGETED":
            return "Point to likely bug. No full solution."

        if level == "SOLUTION":
            return "Explain fix clearly. Small snippets allowed."

        return "Give a helpful hint."

    def _parse_response(self, content: str) -> AIHint:

        try:
            data = json.loads(content)

            return AIHint(
                explanation=data.get("explanation", "").strip(),
                suggestion=data.get("suggestion", "").strip(),
            )

        except Exception:
            return AIHint(
                explanation="Could not parse AI response.",
                suggestion="Review your logic.",
            )

    def _fallback_hint(self, level: str) -> AIHint:

        if level == "BASIC":
            return AIHint(
                explanation="Conceptual issue likely.",
                suggestion="Revisit approach.",
            )

        if level == "TARGETED":
            return AIHint(
                explanation="Specific bug likely present.",
                suggestion="Check edge cases.",
            )

        if level == "SOLUTION":
            return AIHint(
                explanation="Concrete issue in implementation.",
                suggestion="Check imports and outputs.",
            )

        return AIHint(
            explanation="Unable to generate hint.",
            suggestion="Debug step by step.",
        )
