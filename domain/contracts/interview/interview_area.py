# domain/contracts/interview_area.py

from enum import Enum


class InterviewArea(str, Enum):

    # HR interview areas (5)
    HR_BACKGROUND = "hr_background"
    HR_TECHNICAL_KNOWLEDGE = "hr_technical_knowledge"
    HR_SITUATIONAL = "hr_situational"
    HR_BRAIN_TEASER = "hr_brain_teaser"
    HR_ANALYTICAL = "hr_analytical"

    # Technical interview areas (5)
    TECH_BACKGROUND = "technical_background"
    TECH_TECHNICAL_KNOWLEDGE = "technical_technical_knowledge"
    TECH_CASE_STUDY = "technical_case_study"
    TECH_DATABASE = "technical_database"
    TECH_CODING = "technical_coding"
