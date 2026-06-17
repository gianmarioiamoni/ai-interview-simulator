# services/question_corpus/contracts/adaptive_retrieval_context.py

from pydantic import BaseModel

from domain.contracts.question.sql_domain import SqlDomain
from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory


class AdaptiveRetrievalContext(BaseModel):

    current_role: str

    seniority: str

    target_area: str

    target_question_count: int

    already_used_question_ids: list[str] = []

    already_used_domains: list[SqlDomain] = []

    weak_domains: list[SqlDomain] = []

    strong_domains: list[SqlDomain] = []

    target_difficulty: int | None = None

    retrieval_query: str | None = None

    memory: InterviewRetrievalMemory


    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
