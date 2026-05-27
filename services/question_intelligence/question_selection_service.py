# services/question_intelligence/question_selection_service.py

import uuid

from typing import List

from domain.contracts.question.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
)
from domain.contracts.question.generated_question import GeneratedQuestion
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.question.question import SQLTestCase
from domain.contracts.question.question import QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance

from services.question_intelligence.question_retrieval_service import QuestionRetrievalService
from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.coding_question_generator import CodingQuestionGenerator, GeneratedCodingQuestion
from services.question_intelligence.sql_question_generator import SQLQuestionGenerator
from services.question_intelligence.mappers.runtime_question_mapper import RuntimeQuestionMapper
from services.interview_selection.assembled_question import AssembledQuestion
from services.interview_selection.interview_stage import InterviewStage

from app.settings.constants import QUESTIONS_PER_AREA

from app.core.logger import get_logger

logger = get_logger(__name__)


class QuestionSelectionService:
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
        self._runtime_mapper = RuntimeQuestionMapper()

    # =========================================================
    # PUBLIC
    # =========================================================

    def build_area_questions(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        questions_per_area: int = QUESTIONS_PER_AREA,
    ) -> List[Question]:

        # -----------------------------------------------------
        # CODING AREA
        # -----------------------------------------------------

        if area == InterviewArea.TECH_CODING:
            return self._build_coding_questions(
                role=role,
                level=level,
                area=area,
                questions_per_area=questions_per_area,
            )

        # -----------------------------------------------------
        # DATABASE AREA
        # -----------------------------------------------------

        if area == InterviewArea.TECH_DATABASE:
            return self._build_sql_questions(
                role=role,
                level=level,
                area=area,
                questions_per_area=questions_per_area,
            )

        # -----------------------------------------------------
        # STANDARD FLOW
        # -----------------------------------------------------

        questions: List[Question] = []

        # 1. RETRIEVE
        retrieved = self._retrieval_service.retrieve(
            query=self._build_retrieval_query(role, level, area),
            k=questions_per_area,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
        )

        for item in retrieved:
            questions.append(self._runtime_mapper.map_retrieved_bank_item(item))

        # 2. GENERATE (ONLY IF NEEDED) 
        remaining_slots = questions_per_area - len(questions)

        if remaining_slots > 0:
            generated = self._generator.generate(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
                n=remaining_slots,
            )

            for gen in generated:
                questions.append(
                    self._map_generated_question(
                        gen,
                        area=area,
                    )
                )

        return self._select_by_difficulty(questions, questions_per_area)

    # =========================================================
    # SQL PIPELINE
    # =========================================================

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
                f"[SQL] Area {area.value} produced {len(questions)} "
                f"questions, expected {questions_per_area}"
            )

        return questions

    # =========================================================
    # CODING PIPELINE
    # =========================================================

    def _build_coding_questions(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        questions_per_area: int = QUESTIONS_PER_AREA,
    ) -> List[Question]:

        raw_items = self._coding_generator.generate(
            role=role,
            level=level,
            n=questions_per_area,
        )

        questions: List[Question] = []

        for item in raw_items:

            coding_spec = item.coding_spec
            self._validate_alignment(item, coding_spec)

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
                f"[CODING] Area {area.value} produced {len(questions)} "
                f"questions, expected {questions_per_area}"
            )

        return questions

    # =========================================================
    # HELPERS
    # =========================================================

    def _build_retrieval_query(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
    ) -> str:

        return f"""
        {role.value} {level.value} interview question
        topic: {area.value}

        Focus on:
        - diverse concepts
        - different problem types
        - avoid repetition of API questions
        - Ensure each question targets a DIFFERENT concept within the area
        """

    def _validate_alignment(
        self,
        item: GeneratedCodingQuestion,
        spec: CodingSpec,
    ) -> None:

        prompt = item.prompt

        if spec.entrypoint not in prompt:
            raise ValueError(f"Entrypoint '{spec.entrypoint}' not found in prompt")

        for p in spec.parameters:
            if p not in prompt:
                raise ValueError(f"Parameter '{p}' not found in prompt")

