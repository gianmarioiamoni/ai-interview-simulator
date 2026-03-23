# app/ui/response/sections/counter_section.py

from app.ui.dto.question_dto import QuestionDTO


class CounterSection:

    @staticmethod
    def build(
        question: QuestionDTO,
        attempts: int,
        max_attempts: int,
    ) -> str:

        return (
            "### Interview Progress\n\n"
            f"Question {question.index} / {question.total}\n\n"
            f"Area: {question.area}\n\n"
            f"Attempts: {attempts} / {max_attempts}"
        )
