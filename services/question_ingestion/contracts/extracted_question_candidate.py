# services/question_ingestion/contracts/extracted_question_candidate.py

from pydantic import BaseModel


class ExtractedQuestionCandidate(BaseModel):

    text: str

    section_context: str | None = None

    repository_context: str | None = None

    source_file: str | None = None

    line_number: int | None = None

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
