# domain/contracts/interview_level.py

from enum import Enum


class InterviewLevel(str, Enum):
    POOR = "poor"
    AVERAGE = "average"
    STRONG = "strong"
    EXCELLENT = "excellent"
