# services/humanizer/contracts/humanizer_input.py

from pydantic import BaseModel

from domain.contracts.question.question import Question


class HumanizerInput(BaseModel):

    current_question: Question

    previous_question: str | None = None

    previous_answer: str | None = None

    previous_score: float | None = None

    follow_up_count: int = 0

    last_was_follow_up: bool = False

    language: str = "en"

    chat_history: list[str] = []

    model_config = {
        "frozen": True,
    }
