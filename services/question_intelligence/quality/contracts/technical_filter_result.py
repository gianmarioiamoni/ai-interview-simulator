# services/question_quality/contracts/technical_filter_result.py

from pydantic import BaseModel


class TechnicalFilterResult(BaseModel):

    is_technical: bool

    score: float

    matched_categories: list[str]

    matched_terms: list[str]

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
