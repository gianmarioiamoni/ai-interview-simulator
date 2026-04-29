# services/prompt_builders/evaluation_prompt_builder.py

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer

from domain.contracts.question.question import Question
from domain.contracts.interview.answer import Answer


def build_evaluation_prompt(question: Question, answer: Answer) -> str:

    template = PromptLoader.load("evaluation/written_evaluation.txt")

    context = {
        "question": question.prompt,
        "answer": answer.content,
    }

    return PromptRenderer.render(template, context)
