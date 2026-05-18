# services/question_intelligence/hybrid/keyword_search_result.py

from pydantic import BaseModel


class KeywordSearchResult(BaseModel):

    text: str

    score: float

    model_config = {
        "frozen": True,
    }
