# services/question_intelligence/coverage/coverage_bucket.py

from pydantic import BaseModel

from typing import List


class CoverageBucket(BaseModel):

    topic: str

    questions: List[str]

    model_config = {
        "frozen": True,
    }
