# services/question_intelligence/area_question_builder.py

import uuid

from typing import List

from domain.contracts.question.question import (
    Question,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)
from domain.contracts.interview.interview_type import (
    InterviewType,
)

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.question_generator import (
    QuestionGenerator,
)

from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
)

from services.question_intelligence.sql_question_generator import (
    SQLQuestionGenerator,
)

from services.question_intelligence.pipelines.written_question_pipeline import (
    WrittenQuestionPipeline,
)

from services.question_intelligence.pipelines.coding_question_pipeline import (
    CodingQuestionPipeline,
)

from services.question_intelligence.pipelines.sql_question_pipeline import (
    SQLQuestionPipeline,
)

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

from app.settings.constants import QUESTIONS_PER_AREA

from app.core.logger import get_logger

logger = get_logger(__name__)


class AreaQuestionBuilder:

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        generator: QuestionGenerator,
        coding_generator: CodingQuestionGenerator,
        sql_generator: SQLQuestionGenerator,
    ) -> None:

        self._retrieval_service = retrieval_service
        self._generator = generator
        self._coding_generator = coding_generator
        self._sql_generator = sql_generator
        self._written_pipeline = WrittenQuestionPipeline(
            retrieval_service=retrieval_service,
            generator=generator,
        )
        self._coding_pipeline = CodingQuestionPipeline(
            retrieval_service=retrieval_service,
            coding_generator=coding_generator,
        )
        self._sql_pipeline = SQLQuestionPipeline(
            retrieval_service=retrieval_service,
            sql_generator=sql_generator,
        )
    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        questions_per_area: int = QUESTIONS_PER_AREA,
        corpus_quota: int | None = None,
        memory: InterviewRetrievalMemory | None = None,
        job_description: str | None = None,
    ) -> tuple[List[Question], InterviewRetrievalMemory]:
        """
        corpus_quota: maximum number of questions drawn from the retrieval corpus
        for this area. Remaining slots are filled by LLM generation. When None
        the pipeline uses legacy behaviour (corpus fills as much as available).
        """

        session_memory = (
            memory if memory is not None else InterviewRetrievalMemory()
        )

        # -------------------------------------------------
        # CODING
        # -------------------------------------------------

        if area == InterviewArea.TECH_CODING:
            return self._coding_pipeline.build(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
                questions_per_area=questions_per_area,
                memory=session_memory,
                job_description=job_description,
            )

        # -------------------------------------------------
        # SQL
        # -------------------------------------------------

        if area == InterviewArea.TECH_DATABASE:
            return self._sql_pipeline.build(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
                questions_per_area=questions_per_area,
                corpus_quota=corpus_quota,
                memory=session_memory,
                job_description=job_description,
            )

        # -------------------------------------------------
        # WRITTEN
        # -------------------------------------------------

        return self._written_pipeline.build(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            questions_per_area=questions_per_area,
            corpus_quota=corpus_quota,
            memory=session_memory,
            job_description=job_description,
        )



