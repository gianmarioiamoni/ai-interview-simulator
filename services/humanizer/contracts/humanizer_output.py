# services/humanizer/contracts/humanizer_output.py

from pydantic import BaseModel

from services.humanizer.contracts.humanizer_decision import HumanizerDecision


class HumanizerOutput(BaseModel):

    decision: HumanizerDecision

    message: str

    score: int | None = None

    follow_up_used: bool = False

    model_config = {
        "frozen": True,
    }
