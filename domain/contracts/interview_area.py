# domain/contracts/interview_area.py

# Interview area contract
#
# Closed set of interview areas grouped by interview type.
# Immutable and type-safe.

from enum import Enum


class InterviewType(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"


class InterviewArea(str, Enum):
    # HR areas
    HR_BACKGROUND = "hr_background"
    HR_TECHNICAL_KNOWLEDGE = "hr_technical_knowledge"
    HR_SITUATIONAL = "hr_situational"
    HR_BRAIN_TEASER = "hr_brain_teaser"
    HR_ANALYTICAL = "hr_analytical"

    # Technical areas
    TECH_BACKGROUND = "technical_background"
    TECH_TECHNICAL_KNOWLEDGE = "technical_technical_knowledge"
    TECH_CASE_STUDY = "technical_case_study"
    TECH_DATABASE = "technical_database"
    TECH_CODING = "technical_coding"
