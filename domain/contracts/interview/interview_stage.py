# domain/contracts/interview/interview_stage.py

from enum import Enum


class InterviewStage(str, Enum):

    WARMUP = "warmup"

    CORE = "core"

    ADVANCED = "advanced"
