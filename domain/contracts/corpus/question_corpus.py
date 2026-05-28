# domain/contracts/corpus/question_corpus.py

from pydantic import BaseModel

from domain.contracts.corpus.curated_question import CuratedQuestion


class QuestionCorpus(BaseModel):

    questions: list[CuratedQuestion]

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
