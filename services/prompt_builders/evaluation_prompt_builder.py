# services/prompt_builders/evaluation_prompt_builder.py

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer

from domain.contracts.question.question import Question
from domain.contracts.interview.answer import Answer
from domain.contracts.user.role import Role


def build_evaluation_prompt(
    question: Question,
    answer: Answer,
    role: Role | None = None,
    seniority_level: str | None = None,
) -> str:

    template = PromptLoader.load("evaluation/written_evaluation.txt")

    role_label = "unspecified"
    if role is not None:
        role_label = role.custom_name or role.type.value

    context = {
        "question": question.prompt,
        "answer": answer.content,
        "role": role_label,
        "area": question.area.value,
        "question_type": question.type.value,
        "difficulty": question.difficulty.value,
        "seniority_level": seniority_level or "mid",
    }

    return PromptRenderer.render(template, context)
