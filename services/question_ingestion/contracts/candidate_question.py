# services/question_ingestion/contracts/candidate_question.py

from pydantic import BaseModel


class CandidateQuestion(BaseModel):

    text: str

    section_heading: str

    source_file: str

    surrounding_context: str | None = None

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
