# domain/contracts/question/question_runtime_telemetry.py

from pydantic import BaseModel


class QuestionRuntimeTelemetry(BaseModel):

    semantic_similarity_score: float | None = None

    novelty_bonus: float | None = None

    rarity_bonus: float | None = None

    cluster_penalty: float | None = None

    retrieval_score: float | None = None

    recovered_via_replanning: bool = False

    
    model_config = {
        "frozen": True,
    }
