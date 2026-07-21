# domain/contracts/question/interview_retrieval_memory.py

from pydantic import BaseModel

from domain.contracts.question.sql_domain import SqlDomain


class InterviewRetrievalMemory(BaseModel):

    asked_question_ids: list[str] = []

    covered_domains: list[SqlDomain] = []

    weak_domains: list[SqlDomain] = []

    strong_domains: list[SqlDomain] = []

    theme_anchor: str | None = None

    difficulty_history: list[int] = []

    average_score: float = 0.0

    question_count: int = 0

    session_selected_prompts: list[str] = []

    session_used_topics: list[str] = []

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
