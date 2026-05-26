# domain/contracts/question/question_origin_type.py

from enum import Enum


class QuestionOriginType(str, Enum):

    RETRIEVED = "retrieved"

    GENERATED = "generated"

    HYBRID = "hybrid"

    HUMANIZED = "humanized"

    MANUAL = "manual"
