# services/question_ingestion/contracts/raw_question_record.py

from pydantic import BaseModel


class RawQuestionRecord(BaseModel):

    source: str
    raw_payload: dict

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
