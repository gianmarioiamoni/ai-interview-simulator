# services/question_corpus/contracts/adaptive_retrieval_context.py

from pydantic import BaseModel

from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory


class AdaptiveRetrievalContext(BaseModel):

    current_role: str

    seniority: str

    target_area: str

    target_question_count: int

    already_used_question_ids: list[str] = []

    already_used_domains: list[str] = []

    weak_domains: list[str] = []

    strong_domains: list[str] = []

    target_difficulty: int | None = None

    retrieval_query: str | None = None

    memory: InterviewRetrievalMemory


    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
