# services/question_intelligence/lazy_adaptive_interview_service.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.area_question_builder import AreaQuestionBuilder
from services.question_intelligence.interview_area_difficulty_profile import (
    order_areas_by_derived_difficulty,
)
from services.question_intelligence.interview_theme_memory import (
    with_interview_theme_anchor,
)
from services.question_intelligence.interview_theme_selector import InterviewThemeSelector

from app.settings.constants import (
    QUESTIONS_PER_AREA,
    TECHNICAL_AREA_QUESTION_COUNT,
)
from services.question_intelligence.corpus_quota_resolver import resolve_corpus_quota


class LazyAdaptiveInterviewService:

    def __init__(
        self,
        area_builder: AreaQuestionBuilder,
        theme_selector: InterviewThemeSelector | None = None,
    ) -> None:

        self._area_builder = area_builder
        self._theme_selector = (
            theme_selector if theme_selector is not None else InterviewThemeSelector()
        )

    def resolve_planned_areas(
        self,
        interview_type: InterviewType,
    ) -> list[InterviewArea]:

        return order_areas_by_derived_difficulty(interview_type.get_areas())

    def generate_first_question(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        job_description: str | None = None,
    ) -> tuple[list[Question], InterviewRetrievalMemory, list[str]]:

        planned_areas = self.resolve_planned_areas(interview_type)
        memory = InterviewRetrievalMemory()

        theme_anchor = self._theme_selector.select_anchor(
            role=role,
            level=level,
            first_area=planned_areas[0],
        )
        memory = with_interview_theme_anchor(memory, theme_anchor)

        questions, memory = self._area_builder.build(
            role=role,
            level=level,
            interview_type=interview_type,
            area=planned_areas[0],
            questions_per_area=QUESTIONS_PER_AREA,
            corpus_quota=resolve_corpus_quota(planned_areas[0], interview_type, QUESTIONS_PER_AREA),
            memory=memory,
            job_description=job_description,
        )

        return questions[:QUESTIONS_PER_AREA], memory, [area.value for area in planned_areas]

    def generate_next_question(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        planned_areas: list[str],
        generated_count: int,
        memory: InterviewRetrievalMemory,
        job_description: str | None = None,
    ) -> tuple[Question, InterviewRetrievalMemory]:

        if generated_count >= len(planned_areas):
            raise ValueError("All planned areas already have questions")

        next_area = InterviewArea(planned_areas[generated_count])

        questions, memory = self._area_builder.build(
            role=role,
            level=level,
            interview_type=interview_type,
            area=next_area,
            questions_per_area=QUESTIONS_PER_AREA,
            corpus_quota=resolve_corpus_quota(next_area, interview_type, QUESTIONS_PER_AREA),
            memory=memory,
            job_description=job_description,
        )

        if not questions:
            raise ValueError(f"No question generated for area {next_area.value}")

        return questions[0], memory
