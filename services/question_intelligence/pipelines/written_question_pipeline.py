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

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.question_generator import (
    QuestionGenerator,
)

from services.question_intelligence.retrieval_query_builder import (
    RetrievalQueryBuilder,
)

from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.interview_theme_guidance import (
    build_theme_guidance,
)
from services.question_intelligence.interview_theme_memory import (
    get_interview_theme_anchor,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)

from app.settings.constants import (
    QUESTIONS_PER_AREA,
)


class WrittenQuestionPipeline:

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        generator: QuestionGenerator,
    ) -> None:

        self._retrieval_service = retrieval_service
        self._generator = generator

        self._retrieval_query_builder = RetrievalQueryBuilder()

        self._retrieval_strategy_resolver = RetrievalStrategyResolver()

        self._memory_updater = InterviewMemoryUpdater()

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
        memory: InterviewRetrievalMemory | None = None,
    ) -> tuple[List[Question], InterviewRetrievalMemory]:

        session_memory = (
            memory if memory is not None else InterviewRetrievalMemory()
        )

        questions: List[Question] = []

        retrieved_pairs: list[tuple[QuestionBankItem, Question]] = []

        # -------------------------------------------------
        # QUERY
        # -------------------------------------------------

        theme_anchor = get_interview_theme_anchor(session_memory)

        retrieval_query = self._retrieval_query_builder.build(
            role=role,
            level=level,
            area=area,
            theme_anchor=theme_anchor,
        )

        # -------------------------------------------------
        # STRATEGY
        # -------------------------------------------------

        retrieval_strategy = self._retrieval_strategy_resolver.resolve(
            area=area,
            level=level,
            questions_per_area=questions_per_area,
        )

        # -------------------------------------------------
        # RETRIEVAL
        # -------------------------------------------------

        retrieved = self._retrieval_service.retrieve(
            query=retrieval_query,
            retrieval_strategy=retrieval_strategy,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
            memory=session_memory,
        )

        for item in retrieved:

            mapped = self._map_bank_item(
                item,
            )

            retrieved_pairs.append(
                (item, mapped),
            )

            questions.append(
                mapped,
            )

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
                theme_guidance=build_theme_guidance(
                    theme_anchor=theme_anchor,
                    area=area,
                ),
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

        selected = self._select_by_difficulty(
            questions=questions,
            total=questions_per_area,
        )

        selected_prompts = {
            question.prompt for question in selected
        }

        for bank_item, mapped_question in retrieved_pairs:

            if mapped_question.prompt not in selected_prompts:
                continue

            session_memory = self._memory_updater.record_bank_item_selection(
                memory=session_memory,
                item=bank_item,
            )

        return selected, session_memory

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
            provenance=item.provenance,
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
