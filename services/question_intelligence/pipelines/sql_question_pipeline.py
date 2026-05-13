# services/question_intelligence/pipelines/sql_question_pipeline.py

import logging

from typing import List

from domain.contracts.question.question import (
    Question,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.user.role import RoleType

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.sql_question_generator import (
    SQLQuestionGenerator,
)

logger = logging.getLogger(__name__)


class SQLQuestionPipeline:

    def __init__(
        self,
        sql_generator: SQLQuestionGenerator,
    ) -> None:

        self._sql_generator = sql_generator

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        questions_per_area: int,
    ) -> List[Question]:

        questions = self._sql_generator.generate(
            role=role,
            level=level,
            n=questions_per_area,
        )

        if len(questions) < questions_per_area:

            logger.warning(
                f"[SQL] Area {area.value} produced "
                f"{len(questions)} questions "
                f"(expected {questions_per_area})"
            )

        return questions
