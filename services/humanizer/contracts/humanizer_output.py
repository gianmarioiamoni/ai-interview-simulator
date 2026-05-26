# services/humanizer/contracts/humanizer_output.py

from pydantic import BaseModel


class HumanizerOutput(BaseModel):

    humanized_question: str

    remark: str | None = None

    is_follow_up: bool = False

    follow_up_reason: str | None = None

    model_config = {
        "frozen": True,
    }
