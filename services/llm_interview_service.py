# services/llm_interview_service.py

from domain.contracts.question import Question
from infrastructure.llm.openai_client import OpenAIClient


class LLMInterviewService:

    def __init__(self) -> None:
        self._client = OpenAIClient()

    def evaluate_answer(self, question: Question, answer: str) -> str:

        prompt = f"""
        Question:
        {question.prompt}

        Candidate Answer:
        {answer}

        Provide a short professional evaluation (max 5 sentences).
        """

        return self._client.generate_answer(prompt)
