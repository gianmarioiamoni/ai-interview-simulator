# services/question_corpus/contracts/interview_retrieval_memory.py

from pydantic import BaseModel


class InterviewRetrievalMemory(BaseModel):

    asked_question_ids: list[str] = []

    covered_domains: list[str] = []

    weak_domains: list[str] = []

    strong_domains: list[str] = []

    difficulty_history: list[int] = []

    average_score: float = 0.0

    question_count: int = 0

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
