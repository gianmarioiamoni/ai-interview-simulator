# domain/contracts/interview/interview_type.py

from enum import Enum
from typing import List

from domain.contracts.interview.interview_area import InterviewArea


class InterviewType(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"

    # =========================================================
    # DOMAIN LOGIC
    # =========================================================

    def get_areas(self) -> List[InterviewArea]:

        if self == InterviewType.HR:
            return [
                InterviewArea.HR_BACKGROUND,
                InterviewArea.HR_TECHNICAL_KNOWLEDGE,
                InterviewArea.HR_SITUATIONAL,
                InterviewArea.HR_BRAIN_TEASER,
                InterviewArea.HR_ANALYTICAL,
            ]

        if self == InterviewType.TECHNICAL:
            return [
                InterviewArea.TECH_BACKGROUND,
                InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                InterviewArea.TECH_CASE_STUDY,
                InterviewArea.TECH_DATABASE,
                InterviewArea.TECH_CODING,
            ]

        raise ValueError(f"Unsupported interview type: {self}")
