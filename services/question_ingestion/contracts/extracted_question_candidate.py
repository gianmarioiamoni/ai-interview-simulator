from pydantic import BaseModel


class ExtractedQuestionCandidate(BaseModel):

    text: str

    section_context: str | None = None

    repository_context: str | None = None

    source_file: str | None = None

    model_config = {
        "frozen": True,
    }
