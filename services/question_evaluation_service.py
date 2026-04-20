# services/question_evaluation_service.py

import json
import logging
import os

from openai import OpenAI
from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class QuestionEvaluationService:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self._client = OpenAI(api_key=api_key)

    # ---------------------------------------------------------

    def evaluate(
        self,
        question: Question,
        answer_text: str,
    ) -> QuestionEvaluation:

        prompt = self._build_prompt(question, answer_text)

        for attempt in range(MAX_RETRIES + 1):

            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict and demanding FAANG-level technical interviewer.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )

            tokens_used = (
                response.usage.total_tokens if hasattr(response, "usage") else 0
            )

            try:
                parsed = self._extract_json(response.choices[0].message.content)
                parsed["tokens_used"] = tokens_used

                evaluation = QuestionEvaluation.model_validate(parsed)

                return evaluation

            except Exception as e:
                logger.warning(f"question_evaluation_retry_{attempt}: {e}")

                if attempt == MAX_RETRIES:
                    return self._fallback(question)

        return self._fallback(question)

    # ---------------------------------------------------------

    def _build_prompt(self, question: Question, answer_text: str) -> str:

        return f"""
You are evaluating a candidate in a real technical interview.

Question:
{question.prompt}

Candidate answer:
{answer_text}

Return STRICT JSON only.

Format:

{{
  "question_id": "{question.id}",
  "score": float (0-100),
  "max_score": 100,
  "feedback": string,
  "strengths": list of strings,
  "weaknesses": list of strings,
  "passed": boolean
}}

SCORING SYSTEM (STRICT AND ENFORCED):

You must evaluate like a senior interviewer in a top-tier tech company.

Score ranges:

- 90-100 → Exceptional (VERY RARE)
  Deep, precise, complete, with trade-offs and real-world insight

- 75-89 → Good
  Correct and structured, but missing depth OR real-world insight

- 60-74 → Average
  Partial, generic, or somewhat superficial

- 40-59 → Weak
  Significant gaps or incomplete understanding

- 0-39 → Incorrect
  Wrong or irrelevant

ENFORCED PENALTIES:

- If answer is generic → MAX 75
- If no concrete examples → MAX 80
- If missing trade-offs → MAX 78
- If explanation is shallow → MAX 70

CRITICAL CONSTRAINTS:

- Most answers should fall between 60 and 80
- Scores above 85 must be rare
- If the answer has any meaningful weakness → score MUST be below 85
- Scores ≥90 ONLY if the answer is complete, deep, and has no meaningful gaps
- If you mention missing depth → score MUST be ≤ 80

CONSISTENCY RULE:

- The score MUST match the weaknesses
- If weaknesses are present → score MUST reflect them clearly

STRICT RULES:

- score must be between 0 and 100
- max_score must be 100
- no extra fields
- no explanations outside JSON
"""

    # ---------------------------------------------------------

    def _extract_json(self, text: str) -> dict:

        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1:
                raise ValueError("No JSON object found")

            return json.loads(text[start : end + 1])

    # ---------------------------------------------------------

    def _fallback(self, question: Question) -> QuestionEvaluation:

        return QuestionEvaluation(
            question_id=question.id,
            score=50.0,
            max_score=100.0,
            feedback="Fallback evaluation applied.",
            strengths=[],
            weaknesses=[],
            passed=False,
        )
