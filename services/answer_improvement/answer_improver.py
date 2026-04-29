# services/answer_improvement/answer_improver.py

from app.ports.llm_port import LLMPort


from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer

class AnswerImprover:

    def __init__(self, llm: LLMPort):
        self._llm = llm

    def improve(
        self,
        question: str,
        user_answer: str,
        feedback: str,
    ) -> str:

        template = PromptLoader.load("transformation/answer_improver.txt")

        context = {
            "question": question,
            "user_answer": user_answer,
            "feedback": feedback,
        }

        prompt = PromptRenderer.render(template, context)

        try:
            response = self._llm.invoke(prompt)
            return response.content.strip()
        except Exception:
            return ""
