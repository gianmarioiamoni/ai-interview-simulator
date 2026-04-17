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
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType

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

from app.settings.constants import QUESTIONS_PER_AREA


class QuestionSelectionService:
    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        generator: QuestionGenerator,
        coding_generator: CodingQuestionGenerator,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._generator = generator
        self._coding_generator = coding_generator

    # =========================================================
    # PUBLIC
    # =========================================================

    def build_area_questions(
        self,
        role: str,
        level: str,
        interview_type: InterviewType,
        area: InterviewArea,
        questions_per_area: int = QUESTIONS_PER_AREA,
    ) -> List[Question]:

        # -----------------------------------------------------
        # CODING AREA
        # -----------------------------------------------------

        if area == InterviewArea.TECH_CODING:
            return self._build_coding_questions(role, level, area)

        # -----------------------------------------------------
        # STANDARD FLOW
        # -----------------------------------------------------

        # 1. RETRIEVE
        retrieved = self._retrieval_service.retrieve(
            query=f"{role} {area.value}",
            k=questions_per_area,
            role=role,
            level=level,
            interview_type=interview_type.value,
            area=area.value,
        )

        # 2. GENERATE (una sola chiamata)
        total_needed = questions_per_area
        remaining_slots = total_needed - len(questions)
        if remaining_slots > 0:
            generated = self._generator.generate(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
                n=remaining_slots,
            )

            for gen in generated:
                questions.append(self._map_generated_question(gen, area=area))

        questions: List[Question] = []

        # -----------------------------------------------------
        # MAP RETRIEVED
        # -----------------------------------------------------

        for item in retrieved:
            questions.append(self._map_bank_item(item))

        # -----------------------------------------------------
        # MAP GENERATED (slice per evitare duplicati)
        # -----------------------------------------------------

        remaining_slots = total_needed - len(questions)

        for gen in generated[:remaining_slots]:
            questions.append(
                self._map_generated_question(
                    gen,
                    area=area,
                )
            )

        return questions

    # =========================================================
    # CODING PIPELINE
    # =========================================================

    def _build_coding_questions(
        self,
        role: str,
        level: str,
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
                    CodingTestCase(**t.model_dump()) 
                    for t in item.visible_tests
                ],
            )

            questions.append(question)

        return questions

    # =========================================================
    # VALIDATION
    # =========================================================

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

    # =========================================================
    # MAPPERS
    # =========================================================

    def _map_bank_item(self, item: QuestionBankItem) -> Question:
        return Question(
            id=str(uuid.uuid4()),
            area=item.area,
            type=QuestionType.WRITTEN,
            prompt=item.text,
            difficulty=self._map_difficulty(item.difficulty),
        )

    def _map_generated_question(
        self,
        generated: GeneratedQuestion,
        area: InterviewArea,
    ) -> Question:

        return Question(
            id=str(uuid.uuid4()),
            area=area,
            type=QuestionType.WRITTEN,
            prompt=generated.text,
            difficulty=self._map_difficulty(generated.difficulty),
        )

    def _map_difficulty(self, value: int) -> QuestionDifficulty:
        if value <= 2:
            return QuestionDifficulty.EASY
        if value == 3:
            return QuestionDifficulty.MEDIUM
        return QuestionDifficulty.HARD
