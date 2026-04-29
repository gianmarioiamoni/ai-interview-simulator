# services/llm_interview_service.py

from domain.contracts.question.question import Question

from infrastructure.llm.openai_client import OpenAIClient

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer


class LLMInterviewService:

    def __init__(self) -> None:
        self._client = OpenAIClient()

    def evaluate_answer(self, question: Question, answer: str) -> str:

        template = PromptLoader.load("evaluation/short_evaluation.txt")

        context = {
            "question": question.prompt,
            "answer": answer,
        }

        prompt = PromptRenderer.render(template, context)

        return self._client.generate_answer(prompt)
