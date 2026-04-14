# services/interview_scoring/dimension_mapper.py

from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType


AREA_TO_DIMENSION = {
    "technical_background": PerformanceDimensionType.TECHNICAL_DEPTH,
    "technical_technical_knowledge": PerformanceDimensionType.TECHNICAL_DEPTH,
    "technical_database": PerformanceDimensionType.TECHNICAL_DEPTH,
    "technical_coding": PerformanceDimensionType.PROBLEM_SOLVING,
    "technical_case_study": PerformanceDimensionType.SYSTEM_DESIGN,
    "hr_background": PerformanceDimensionType.COMMUNICATION,
    "hr_technical_knowledge": PerformanceDimensionType.TECHNICAL_DEPTH,
    "hr_situational": PerformanceDimensionType.COMMUNICATION,
    "hr_brain_teaser": PerformanceDimensionType.PROBLEM_SOLVING,
    "hr_analytical": PerformanceDimensionType.PROBLEM_SOLVING,
}
