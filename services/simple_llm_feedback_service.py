# services/simple_llm_feedback_service.py

# Minimal LLM feedback service
# Used only to validate real LLM integration pipeline

from infrastructure.llm.llm_factory import get_llm
from domain.contracts.question import Question


class SimpleLLMFeedbackService:

    def __init__(self) -> None:
        self._llm = get_llm()

    def generate_feedback(self, question: Question, answer: str) -> str:

        prompt = f"""
You are a senior technical interviewer.

Question:
{question.prompt}

Candidate answer:
{answer}

Provide:
- A short professional evaluation (max 5 sentences)
- One strength
- One improvement suggestion

Be concise.
"""

        response = self._llm.invoke(prompt)

        return response.content.strip()
