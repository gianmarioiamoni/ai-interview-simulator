# services/humanizer/contracts/humanizer_input.py

from pydantic import BaseModel

from domain.contracts.question.question import Question


class HumanizerInput(BaseModel):

    current_question: Question

    previous_question: str | None = None

    previous_answer: str | None = None

    previous_score: float | None = None

    previous_area: str | None = None

    follow_up_count: int = 0

    language: str = "en"

    chat_history: list[str] = []

    last_answer: str | None = None

    last_answer_score: int | None = None

    last_turn_was_follow_up: bool = False

    
    model_config = {
        "frozen": True,
    }
