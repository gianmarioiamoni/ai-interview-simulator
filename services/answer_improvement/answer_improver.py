# services/answer_improvement/answer_improver.py

from app.ports.llm_port import LLMPort
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import ANSWER_IMPROVEMENT


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
        role: str = "unspecified",
        area: str = "unspecified",
        weaknesses: list[str] | None = None,
    ) -> str:

        template = PromptLoader.load("transformation/answer_improver.txt")

        weaknesses_text = (
            "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "None provided"
        )

        context = {
            "question": question,
            "user_answer": user_answer,
            "feedback": feedback,
            "role": role,
            "area": area,
            "weaknesses": weaknesses_text,
        }

        prompt = PromptRenderer.render(template, context)

        try:
            with LLMOperationContext.scope(ANSWER_IMPROVEMENT):
                response = self._llm.invoke(prompt)
            return response.content.strip()
        except Exception:
            return ""
