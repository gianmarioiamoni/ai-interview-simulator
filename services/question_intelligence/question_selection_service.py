# services/question_intelligence/question_selection_service.py

# QuestionSelectionService
#
# Responsibility:
# Combines semantic retrieval and LLM generation
# to produce a complete set of interview questions per area.

import uuid
from typing import List

from domain.contracts.question import Question, QuestionType
from domain.contracts.generated_question import GeneratedQuestion
from domain.contracts.question_bank_item import QuestionBankItem

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.question_generator import (
    QuestionGenerator,
)


class QuestionSelectionService:
    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        generator: QuestionGenerator,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._generator = generator

    def build_area_questions(
        self,
        role: str,
        level: str,
        interview_type: str,
        area: str,
    ) -> List[Question]:

        # 2 from RAG
        retrieved = self._retrieval_service.retrieve(
            query=f"{role} {area}",
            k=2,
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
        )

        # 2 generated
        generated = self._generator.generate(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            n=2,
        )

        questions: List[Question] = []

        # Map retrieved
        for item in retrieved:
            questions.append(self._map_bank_item(item))

        # Map generated
        for gen in generated:
            questions.append(
                self._map_generated_question(
                    gen,
                    area=area,
                    interview_type=interview_type,
                )
            )

        return questions

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
