# services/ai_hint_engine/ai_hint_service.py

from domain.contracts.ai_hint import AIHintInput, AIHint
from infrastructure.llm.llm_factory import get_llm


class AIHintService:

    def __init__(self):
        self._llm = get_llm()

    def generate_hint(self, input_data: AIHintInput) -> AIHint:

        prompt = self._build_prompt(input_data)

        response = self._llm.invoke(prompt)

        content = response.content.strip()

        return self._parse_response(content)

    # =========================================================

    def _build_prompt(self, input_data: AIHintInput) -> str:

        return f"""
You are a senior Python interviewer helping a candidate.

Your goal:
- Explain the error clearly
- Suggest how to fix it
- DO NOT provide full solution code

---

User code:
{input_data.user_code}

---

Error:
{input_data.error}

---

Failed tests:
{input_data.failed_tests}

---

Respond in JSON:

{{
  "explanation": "...",
  "suggestion": "..."
}}
"""

    # =========================================================

    def _parse_response(self, content: str) -> AIHint:

        import json

        try:
            data = json.loads(content)
            return AIHint(
                explanation=data.get("explanation", ""),
                suggestion=data.get("suggestion", ""),
            )
        except Exception:
            return AIHint(
                explanation="Could not generate explanation.",
                suggestion="Try reviewing your logic and edge cases.",
            )
