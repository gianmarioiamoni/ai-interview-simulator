# services/question_intelligence/pipelines/written_question_pipeline.py

import uuid

from typing import List

from domain.contracts.question.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
)

from domain.contracts.question.generated_question import (
    GeneratedQuestion,
)

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
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

from app.settings.constants import QUESTIONS_PER_AREA


class WrittenQuestionPipeline:

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        generator: QuestionGenerator,
    ) -> None:

        self._retrieval_service = retrieval_service
        self._generator = generator

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

        questions: List[Question] = []

        # -------------------------------------------------
        # RETRIEVAL
        # -------------------------------------------------

        retrieved = self._retrieval_service.retrieve(
            query=self._build_retrieval_query(
                role,
                level,
                area,
            ),
            k=questions_per_area,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
        )

        for item in retrieved:
            questions.append(self._map_bank_item(item))

        # -------------------------------------------------
        # GENERATION
        # -------------------------------------------------

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
                        generated=gen,
                        area=area,
                    )
                )

        # -------------------------------------------------
        # BALANCING
        # -------------------------------------------------

        return self._select_by_difficulty(
            questions=questions,
            total=questions_per_area,
        )

    # =====================================================
    # RETRIEVAL QUERY
    # =====================================================

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

    # =====================================================
    # MAPPERS
    # =====================================================

    def _map_bank_item(
        self,
        item: QuestionBankItem,
    ) -> Question:

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

    # =====================================================
    # DIFFICULTY
    # =====================================================

    def _map_difficulty(
        self,
        value: int,
    ) -> QuestionDifficulty:

        if value <= 2:
            return QuestionDifficulty.EASY

        if value == 3:
            return QuestionDifficulty.MEDIUM

        return QuestionDifficulty.HARD

    def _select_by_difficulty(
        self,
        questions: List[Question],
        total: int,
    ) -> List[Question]:

        buckets = {
            QuestionDifficulty.EASY: [],
            QuestionDifficulty.MEDIUM: [],
            QuestionDifficulty.HARD: [],
        }

        for q in questions:
            buckets[q.difficulty].append(q)

        target = {
            QuestionDifficulty.EASY: int(total * 0.2),
            QuestionDifficulty.MEDIUM: int(total * 0.6),
            QuestionDifficulty.HARD: int(total * 0.2),
        }

        selected: List[Question] = []

        for diff, count in target.items():
            selected.extend(buckets[diff][:count])

        if len(selected) < total:

            remaining = [q for q in questions if q not in selected]

            selected.extend(remaining[: total - len(selected)])

        return selected[:total]
