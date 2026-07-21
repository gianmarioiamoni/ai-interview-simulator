# domain/contracts/question/ingestion_metadata.py

from datetime import datetime

from pydantic import BaseModel


class IngestionMetadata(BaseModel):

    source_name: str

    source_type: str

    dataset_version: str

    ingestion_timestamp: datetime

    model_config = {
        "frozen": True,
    }
