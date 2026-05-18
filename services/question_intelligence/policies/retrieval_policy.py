# services/question_intelligence/policies/retrieval_policy.py

from pydantic import BaseModel


class RetrievalPolicy(BaseModel):

    max_questions_per_topic: int

    redundancy_threshold: float

    target_diversity: float

    prioritize_scalability: bool

    prioritize_fundamentals: bool

    prioritize_system_design: bool

    model_config = {
        "frozen": True,
    }
