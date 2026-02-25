# services/simple_llm_feedback_service.py

import os
from openai import OpenAI
from domain.contracts.question import Question


class SimpleLLMFeedbackService:

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self._client = OpenAI(api_key=api_key)

    def generate_feedback(self, question: Question, answer: str) -> str:

        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior technical interviewer.",
                },
                {
                    "role": "user",
                    "content": f"""
Question:
{question.prompt}

Candidate answer:
{answer}

Provide:
- Short professional evaluation (max 5 sentences)
- One strength
- One improvement suggestion
""",
                },
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()
