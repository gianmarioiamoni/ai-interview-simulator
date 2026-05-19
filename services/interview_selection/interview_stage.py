# services/interview_selection/interview_stage.py

from enum import Enum


class InterviewStage(str, Enum):

    WARMUP = "warmup"

    CORE = "core"

    ADVANCED = "advanced"
