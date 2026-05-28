# services/question_corpus/contracts/curated_corpus.py

from pydantic import BaseModel

from domain.contracts.corpus.curated_question import CuratedQuestion


class CuratedCorpus(BaseModel):

    questions: list[CuratedQuestion]

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
