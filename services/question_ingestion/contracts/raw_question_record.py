# services/question_ingestion/contracts/raw_question_record.py

from pydantic import BaseModel


class RawQuestionRecord(BaseModel):

    source: str

    source_type: str

    dataset_version: str

    raw_payload: dict

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

    # TODO:
    # add ingestion_batch_id
    # add dataset_name
    # add dataset_origin_url
