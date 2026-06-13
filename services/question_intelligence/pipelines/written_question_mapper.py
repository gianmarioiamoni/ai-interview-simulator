# services/question_intelligence/pipelines/written_question_mapper.py

import uuid

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.question.generated_question import GeneratedQuestion
from domain.contracts.question.question_bank_item import QuestionBankItem


class WrittenQuestionMapper:
    """
    Maps raw corpus and generated items to Question DTOs for the written pipeline.

    Owns the difficulty integer → QuestionDifficulty enum translation so that
    WrittenQuestionPipeline has no mapping logic inline.
    """

    def from_bank_item(self, item: QuestionBankItem) -> Question:
        return Question(
            id=str(uuid.uuid4()),
            area=item.area,
            type=QuestionType.WRITTEN,
            prompt=item.text,
            difficulty=self._map_difficulty(item.difficulty),
            provenance=item.provenance,
        )

    def from_generated(
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

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    @staticmethod
    def _map_difficulty(value: int) -> QuestionDifficulty:
        if value <= 2:
            return QuestionDifficulty.EASY
        if value == 3:
            return QuestionDifficulty.MEDIUM
        return QuestionDifficulty.HARD
