# infrastructure/llm/openai_client.py

# Minimal OpenAI client wrapper for GPT-4o-mini

from openai import OpenAI

from infrastructure.config.settings import settings


class OpenAIClient:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self._client = OpenAI(api_key=settings.openai_api_key)

    def generate_answer(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=settings.chat_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior technical interviewer.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=settings.openai_client_temperature,
        )

        return response.choices[0].message.content.strip()
