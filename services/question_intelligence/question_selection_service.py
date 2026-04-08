# services/question_intelligence/question_selection_service.py

import uuid
from typing import List

from domain.contracts.question import Question, QuestionType
from domain.contracts.generated_question import GeneratedQuestion
from domain.contracts.question_bank_item import QuestionBankItem
from domain.contracts.coding_test_case import CodingTestCase
from domain.contracts.coding_spec import CodingSpec

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.question_generator import (
    QuestionGenerator,
)
from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
)


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

    def build_area_questions(
        self,
        role: str,
        level: str,
        interview_type: str,
        area: str,
    ) -> List[Question]:

        # -----------------------------------------------------
        # CODING AREA → dedicated pipeline
        # -----------------------------------------------------

        if area == "TECH_CODING":
            return self._build_coding_questions(role, level, area)

        # -----------------------------------------------------
        # STANDARD FLOW (WRITTEN)
        # -----------------------------------------------------

        retrieved = self._retrieval_service.retrieve(
            query=f"{role} {area}",
            k=2,
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
        )

        generated = self._generator.generate(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            n=2,
        )

        questions: List[Question] = []

        for item in retrieved:
            questions.append(self._map_bank_item(item))

        for gen in generated:
            questions.append(
                self._map_generated_question(
                    gen,
                    area=area,
                    interview_type=interview_type,
                )
            )

        return questions

    # =========================================================
    # CODING PIPELINE (NEW)
    # =========================================================

    def _build_coding_questions(
        self,
        role: str,
        level: str,
        area: str,
    ) -> List[Question]:

        raw_items = self._coding_generator.generate(
            role=role,
            level=level,
            n=2,
        )

        questions: List[Question] = []

        for item in raw_items:

            # -------------------------
            # HARD VALIDATION
            # -------------------------

            coding_spec = CodingSpec(**item["coding_spec"])

            # -------------------------
            # ALIGNMENT VALIDATION
            # -------------------------

            self._validate_alignment(item, coding_spec)

            # -------------------------
            # MAPPING → DOMAIN
            # -------------------------

            question = Question(
                id=str(uuid.uuid4()),
                area=area,
                type=QuestionType.CODING,
                prompt=item["prompt"],
                coding_spec=coding_spec,
                visible_tests=[CodingTestCase(**t) for t in item["visible_tests"]],
            )

            questions.append(question)

        return questions

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_alignment(
        self,
        item: dict,
        spec: CodingSpec,
    ) -> None:

        prompt = item["prompt"]

        # entrypoint must be in prompt
        if spec.entrypoint not in prompt:
            raise ValueError(f"Entrypoint '{spec.entrypoint}' not found in prompt")

        # parameters must be in prompt
        for p in spec.parameters:
            if p not in prompt:
                raise ValueError(f"Parameter '{p}' not found in prompt")

    # =========================================================
    # LEGACY MAPPERS (UNCHANGED)
    # =========================================================

    def _map_bank_item(self, item: QuestionBankItem) -> Question:
        return Question(
            id=str(uuid.uuid4()),
            area=item.area,
            type=QuestionType.WRITTEN,
            prompt=item.text,
            difficulty=item.difficulty,
        )

    def _map_generated_question(
        self,
        generated: GeneratedQuestion,
        area: str,
        interview_type: str,
    ) -> Question:

        return Question(
            id=str(uuid.uuid4()),
            area=area,
            type=QuestionType.WRITTEN,
            prompt=generated.text,
            difficulty=generated.difficulty,
        )
