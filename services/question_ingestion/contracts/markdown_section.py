# services/question_ingestion/contracts/markdown_section.py

from pydantic import BaseModel


class MarkdownSection(BaseModel):

    heading: str

    content: str

    level: int

    source_path: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
