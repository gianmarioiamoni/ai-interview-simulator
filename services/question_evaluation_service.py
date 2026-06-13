# services/question_evaluation_service.py

import json
import os

from openai import OpenAI
from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from app.core.logger import get_logger

logger = get_logger(__name__)

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
        system_prompt = PromptLoader.load("evaluation/question_evaluation_system.txt")

        for attempt in range(MAX_RETRIES + 1):

            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
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

        template = PromptLoader.load("evaluation/question_evaluation_user.txt")

        return PromptRenderer.render(
            template,
            {
                "question_id": question.id,
                "question_prompt": question.prompt,
                "answer_text": answer_text,
            },
        )

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
