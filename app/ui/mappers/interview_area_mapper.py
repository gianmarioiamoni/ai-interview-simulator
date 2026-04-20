# app/ui/mappers/interview_area_mapper.py

from domain.contracts.interview.interview_area import InterviewArea


class InterviewAreaMapper:

    LABELS = {
        InterviewArea.TECH_TECHNICAL_KNOWLEDGE: "Technical Knowledge",
        InterviewArea.TECH_DATABASE: "Database",
        InterviewArea.TECH_CODING: "Coding",
        InterviewArea.TECH_CASE_STUDY: "System Design",
        InterviewArea.TECH_BACKGROUND: "Technical Background",
        InterviewArea.HR_TECHNICAL_KNOWLEDGE: "Technical Knowledge",
        InterviewArea.HR_SITUATIONAL: "Behavioral",
        InterviewArea.HR_BRAIN_TEASER: "Problem Solving",
        InterviewArea.HR_ANALYTICAL: "Analytical Thinking",
        InterviewArea.HR_BACKGROUND: "Background",
    }

    @classmethod
    def to_label(cls, area: InterviewArea) -> str:
        return cls.LABELS.get(
            area,
            area.value.replace("_", " ").title(),
        )
