# services/ai_hint_engine/ai_hint_service.py

import json
from typing import Optional
from domain.contracts.ai_hint import AIHintInput, AIHint
from infrastructure.llm.llm_factory import get_llm


class AIHintService:

    def __init__(self):
        self._llm = get_llm()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def generate_hint(
        self,
        input_data: AIHintInput,
        level: Optional[str] = None,  # BASIC | TARGETED | SOLUTION
    ) -> AIHint:

        level = level or input_data.hint_level.value
        prompt = self._build_prompt(input_data, level)

        try:
            response = self._llm.invoke(prompt)
            content = response.content.strip()
            return self._parse_response(content)

        except Exception:
            return self._fallback_hint(level)

    # =========================================================
    # PROMPT BUILDER
    # =========================================================

    def _build_prompt(self, input_data: AIHintInput, level: str) -> str:

        level_instruction = self._get_level_instruction(level)

        return f"""
You are a senior Python interviewer helping a candidate debug their solution.

Your goal:
- Help the candidate understand what is wrong
- Guide them toward a fix
- Adapt your explanation based on the hint level

---

HINT LEVEL:
{level}

INSTRUCTIONS:
{level_instruction}

---

QUESTION:
{input_data.question}

---

USER CODE:
{input_data.user_code}

---

ERROR:
{input_data.error}

---

FAILED TESTS:
{input_data.failed_tests}

---

RULES:
- Be clear and concise
- Do NOT hallucinate requirements
- Focus only on the actual problem
- Output STRICT JSON only

---

FORMAT:

{{
  "explanation": "...",
  "suggestion": "..."
}}
"""

    # =========================================================
    # LEVEL STRATEGY
    # =========================================================

    def _get_level_instruction(self, level: str) -> str:

        if level == "BASIC":
            return """
- Give a high-level hint
- Do NOT point to exact line of code
- Do NOT provide code
- Focus on conceptual mistake
"""

        if level == "TARGETED":
            return """
- Be more specific about the bug
- Point to the likely problematic area
- You may reference parts of the logic
- Do NOT provide full solution code
"""

        if level == "SOLUTION":
            return """
- Provide a clear explanation of the issue
- Explain exactly what needs to change
- You MAY include small code snippets
- Do NOT dump a full solution
"""

        # fallback safety
        return "Give a helpful debugging hint."

    # =========================================================
    # PARSER
    # =========================================================

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
                suggestion="Review your logic and test edge cases.",
            )

    # =========================================================
    # FALLBACK
    # =========================================================

    def _fallback_hint(self, level: str) -> AIHint:

        if level == "BASIC":
            return AIHint(
                explanation="There is likely a conceptual issue in your approach.",
                suggestion="Revisit the problem requirements and your logic.",
            )

        if level == "TARGETED":
            return AIHint(
                explanation="There is likely a specific bug in your implementation.",
                suggestion="Check how your function handles edge cases or data structures.",
            )

        if level == "SOLUTION":
            return AIHint(
                explanation="Your implementation likely has a concrete issue.",
                suggestion="Carefully review imports, edge cases, and expected outputs.",
            )

        return AIHint(
            explanation="Unable to generate hint.",
            suggestion="Try debugging step by step.",
        )
