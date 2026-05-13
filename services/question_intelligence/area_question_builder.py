# services/question_intelligence/area_question_builder.py

import uuid
import logging

from typing import List

from domain.contracts.question.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    SQLTestCase,
)
from domain.contracts.question.generated_question import GeneratedQuestion
from domain.contracts.question.question_bank_item import QuestionBankItem

from domain.contracts.execution.coding_test_case import (
    CodingTestCase,
)
from domain.contracts.execution.coding_spec import CodingSpec

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
    GeneratedCodingQuestion,
)

from services.question_intelligence.sql_question_generator import (
    SQLQuestionGenerator,
)

from services.question_intelligence.pipelines.written_question_pipeline import (
    WrittenQuestionPipeline,
)

from app.settings.constants import QUESTIONS_PER_AREA

logger = logging.getLogger(__name__)


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
    ) -> List[Question]:

        # -------------------------------------------------
        # CODING
        # -------------------------------------------------

        if area == InterviewArea.TECH_CODING:
            return self._build_coding_questions(
                role=role,
                level=level,
                area=area,
                questions_per_area=questions_per_area,
            )

        # -------------------------------------------------
        # SQL
        # -------------------------------------------------

        if area == InterviewArea.TECH_DATABASE:
            return self._build_sql_questions(
                role=role,
                level=level,
                area=area,
                questions_per_area=questions_per_area,
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
        )

    # =====================================================
    # SQL PIPELINE
    # =====================================================

    def _build_sql_questions(
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
                f"{len(questions)} questions, "
                f"expected {questions_per_area}"
            )

        return questions

    # =====================================================
    # CODING PIPELINE
    # =====================================================

    def _build_coding_questions(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        questions_per_area: int,
    ) -> List[Question]:

        raw_items = self._coding_generator.generate(
            role=role,
            level=level,
            n=questions_per_area,
        )

        questions: List[Question] = []

        for item in raw_items:

            coding_spec = item.coding_spec

            self._validate_alignment(
                item,
                coding_spec,
            )

            question = Question(
                id=str(uuid.uuid4()),
                area=area,
                type=QuestionType.CODING,
                prompt=item.prompt,
                coding_spec=coding_spec,
                visible_tests=[
                    CodingTestCase(**t.model_dump()) for t in item.visible_tests
                ],
            )

            questions.append(question)

        if len(questions) < questions_per_area:
            logger.warning(
                f"[CODING] Area {area.value} produced "
                f"{len(questions)} questions, "
                f"expected {questions_per_area}"
            )

        return questions
