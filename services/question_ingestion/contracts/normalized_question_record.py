# services/question_ingestion/contracts/normalized_question_record.py

from pydantic import BaseModel


class NormalizedQuestionRecord(BaseModel):

    text: str

    role_hint: str | None = None
    area_hint: str | None = None
    level_hint: str | None = None

    difficulty_hint: int | None = None

    source: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
