# services/question_ingestion/contracts/dataset_descriptor.py

from pydantic import BaseModel


class DatasetDescriptor(BaseModel):

    name: str

    source_type: str

    domain: str

    description: str

    expected_schema: dict[str, str]

    quality_score: float

    trusted: bool

    adapter_name: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
