# services/question_ingestion/contracts/raw_question_record.py

from pydantic import BaseModel


class RawQuestionRecord(BaseModel):

    source: str

    source_type: str

    dataset_version: str

    canonical_payload: dict
    raw_payload: dict

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

    # Roadmap: extend with ingestion_batch_id, dataset_name, dataset_origin_url
    # when multi-source provenance tracking is required.
