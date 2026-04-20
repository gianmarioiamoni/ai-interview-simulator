# services/question_evaluation_service.py

import json
import logging
import os

from openai import OpenAI

from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation
from services.score_calibration_service import ScoreCalibrationService

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class QuestionEvaluationService:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self._client = OpenAI(api_key=api_key)

        self._calibration = ScoreCalibrationService()

    # ---------------------------------------------------------

    def evaluate(
        self,
        question: Question,
        answer_text: str,
    ) -> QuestionEvaluation:

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

SCORING GUIDELINES (STRICT):

You must evaluate like a real senior interviewer in a top tech company.

Score ranges:

- 90-100 → Exceptional (rare)
  - Deep, precise, complete, with trade-offs and real-world insight

- 75-89 → Good
  - Correct and solid, but missing depth, edge cases, or trade-offs

- 60-74 → Average
  - Partially correct, superficial, lacks depth or clarity

- 40-59 → Weak
  - Major gaps, misunderstandings, or incomplete reasoning

- 0-39 → Incorrect
  - Fundamentally wrong or irrelevant

CRITICAL RULES:

- DO NOT give scores above 90 unless the answer is truly exceptional
- Missing depth MUST reduce the score significantly (at least -10)
- Generic answers MUST NOT score above 75
- If no real examples or trade-offs are provided → max 80
- If explanation is shallow → max 70
- Be critical, not polite

Consistency rules:

- If weaknesses are significant → score MUST reflect it
- strengths and weaknesses must justify the score

Return STRICT JSON only.
"""

        for attempt in range(MAX_RETRIES + 1):

            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict and demanding FAANG-level interviewer.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )

            tokens_used = response.usage.total_tokens if hasattr(response, "usage") else 0

            try:
                parsed = self._extract_json(response.choices[0].message.content)
                parsed["tokens_used"] = tokens_used
                evaluation = QuestionEvaluation.model_validate(parsed)
                evaluation = self._calibration.calibrate(evaluation)
                return evaluation

            except Exception as e:
                logger.warning(f"question_evaluation_retry_{attempt}: {e}")

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
