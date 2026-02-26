# services/question_evaluation_service.py

import json
import logging
import os

from openai import OpenAI
from domain.contracts.question import Question
from domain.contracts.question_evaluation import QuestionEvaluation

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class QuestionEvaluationService:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self._client = OpenAI(api_key=api_key)

    # ---------------------------------------------------------

    def evaluate(self, question: Question, answer_text: str) -> QuestionEvaluation:

        prompt = f"""
You are a strict technical interviewer.

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

Rules:
- score must be between 0 and 100
- max_score must be 100
- no extra fields
"""

        for attempt in range(MAX_RETRIES + 1):

            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise evaluator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )

            try:
                parsed = self._extract_json(response.choices[0].message.content)
                evaluation = QuestionEvaluation.model_validate(parsed)
                return evaluation

            except Exception as e:
                logger.warning(f"Question evaluation retry {attempt}: {e}")

                if attempt == MAX_RETRIES:
                    return self._fallback(question)

        return self._fallback(question)

    # ---------------------------------------------------------

    def _extract_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("No JSON found")
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
