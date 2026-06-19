# domain/contracts/interview_state/last_question_context.py

from pydantic import BaseModel

from domain.contracts.question.question import QuestionType


class LastQuestionContext(BaseModel):
    """Snapshot of the departing question captured in navigation_node before
    current_question_index advances. Used by question_node to populate
    HumanizerInput.previous_* fields."""

    question_id: str
    question_prompt: str
    question_type: QuestionType
    question_area: str | None = None
    answer_content: str | None = None
    quality_rank: int | None = None

    model_config = {"frozen": True}
