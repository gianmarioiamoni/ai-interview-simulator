# infrastructure/llm/openai_client.py

# Minimal OpenAI client wrapper for GPT-4o-mini

import os
from openai import OpenAI


class OpenAIClient:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self._client = OpenAI(api_key=api_key)

    def generate_answer(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior technical interviewer.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()
