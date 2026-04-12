# domain/contracts/interview_type.py

from enum import Enum


class InterviewType(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"
