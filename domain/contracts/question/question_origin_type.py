# domain/contracts/question/question_origin_type.py

from enum import Enum


class QuestionOriginType(str, Enum):

    RETRIEVAL = "retrieval"

    LLM_GENERATED = "llm_generated"

    HYBRID = "hybrid"

    FOLLOW_UP = "follow_up"

    HUMANIZED = "humanized"

    RECOVERY_EXPANSION = "recovery_expansion"
