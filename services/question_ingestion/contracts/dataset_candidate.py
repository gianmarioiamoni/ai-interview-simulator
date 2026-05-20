# services/question_ingestion/contracts/dataset_candidate.py

from pydantic import BaseModel


class DatasetCandidate(BaseModel):

    name: str

    source: str

    domain: str

    description: str

    estimated_quality: float

    estimated_noise: float

    adapter_name: str

    ingestion_status: str

    notes: str | None = None

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
