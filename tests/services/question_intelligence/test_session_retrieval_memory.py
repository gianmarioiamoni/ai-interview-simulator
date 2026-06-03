# tests/services/question_intelligence/test_session_retrieval_memory.py

from unittest.mock import MagicMock

import pytest

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.area_question_builder import AreaQuestionBuilder
from services.question_intelligence.pipelines.written_question_pipeline import (
    WrittenQuestionPipeline,
)
from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.question_set_builder import QuestionSetBuilder
from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator
from services.question_intelligence.quality.question_set_quality_analyzer import (
    QuestionSetQualityAnalyzer,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


QUESTION_A_ID = "corpus_question_a"
QUESTION_B_ID = "corpus_question_b"


def _build_bank_item(
    question_id: str,
    text: str,
    area: InterviewArea,
    difficulty: int = 3,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=question_id,
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=area,
        level=SeniorityLevel.MID,
        difficulty=difficulty,
        ingestion_metadata=IngestionMetadata(
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp="2020-01-01T00:00:00Z",
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
        ),
    )


ITEM_A = _build_bank_item(
    QUESTION_A_ID,
    "How would you design a scalable notification system?",
    InterviewArea.TECH_CASE_STUDY,
    difficulty=3,
)

ITEM_B = _build_bank_item(
    QUESTION_B_ID,
    "How would you optimize a slow SQL query?",
    InterviewArea.TECH_DATABASE,
    difficulty=3,
)


def test_written_pipeline_second_area_does_not_reuse_first_selection() -> None:

    retrieval_service = MagicMock(
        spec=QuestionRetrievalService,
    )

    memories_at_retrieve: list[InterviewRetrievalMemory | None] = []

    def retrieve_side_effect(
        *args,
        memory=None,
        **kwargs,
    ) -> list[QuestionBankItem]:

        memories_at_retrieve.append(memory)

        if memory and QUESTION_A_ID in memory.asked_question_ids:
            return [ITEM_B]

        return [ITEM_A, ITEM_B]

    retrieval_service.retrieve.side_effect = retrieve_side_effect

    generator = MagicMock(
        spec=QuestionGenerator,
    )
    generator.generate.return_value = []

    pipeline = WrittenQuestionPipeline(
        retrieval_service=retrieval_service,
        generator=generator,
    )

    memory = InterviewRetrievalMemory()

    first_questions, memory = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_CASE_STUDY,
        questions_per_area=1,
        memory=memory,
    )

    assert len(first_questions) == 1
    assert first_questions[0].prompt == ITEM_A.text
    assert QUESTION_A_ID in memory.asked_question_ids

    second_questions, memory = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=1,
        memory=memory,
    )

    assert len(second_questions) == 1
    assert second_questions[0].prompt == ITEM_B.text
    assert QUESTION_A_ID in memory.asked_question_ids
    assert QUESTION_B_ID in memory.asked_question_ids

    assert memories_at_retrieve[0].asked_question_ids == []
    assert QUESTION_A_ID in memories_at_retrieve[1].asked_question_ids

    second_call_items = retrieval_service.retrieve.call_args_list[1].kwargs.get(
        "memory",
    ) or retrieval_service.retrieve.call_args_list[1][1].get("memory")

    assert QUESTION_A_ID in second_call_items.asked_question_ids


def test_question_set_builder_threads_memory_across_areas() -> None:

    area_builder = MagicMock(
        spec=AreaQuestionBuilder,
    )

    memories_seen: list[InterviewRetrievalMemory] = []

    def build_side_effect(
        *args,
        memory=None,
        area=None,
        **kwargs,
    ) -> tuple[list[Question], InterviewRetrievalMemory]:

        safe_memory = memory if memory is not None else InterviewRetrievalMemory()

        memories_seen.append(safe_memory)

        area_value = area.value if area is not None else "unknown"

        question = Question(
            id=f"q-{area_value}",
            area=area_value,
            type=QuestionType.WRITTEN,
            prompt=f"Prompt for {area_value}",
            difficulty=QuestionDifficulty.MEDIUM,
        )

        updated_memory = safe_memory.model_copy(
            update={
                "asked_question_ids": [
                    *safe_memory.asked_question_ids,
                    f"corpus-{area_value}",
                ],
            },
        )

        return [question], updated_memory

    area_builder.build.side_effect = build_side_effect

    deduplicator = MagicMock(
        spec=SemanticDeduplicator,
    )
    deduplicator.deduplicate.side_effect = lambda questions: questions

    quality_analyzer = MagicMock(
        spec=QuestionSetQualityAnalyzer,
    )
    quality_analyzer.analyze.return_value = MagicMock(
        similarity=MagicMock(
            average_similarity=0.0,
            max_similarity=0.0,
            duplicate_pairs=0,
        ),
        diversity=MagicMock(
            diversity_score=1.0,
        ),
        coverage=MagicMock(
            area_coverage_score=1.0,
            difficulty_balance_score=1.0,
        ),
    )

    builder = QuestionSetBuilder(
        area_builder=area_builder,
        deduplicator=deduplicator,
        quality_analyzer=quality_analyzer,
    )

    areas = [
        InterviewArea.TECH_CASE_STUDY,
        InterviewArea.TECH_DATABASE,
    ]

    result = builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        areas=areas,
        questions_per_area=1,
    )

    assert len(result) == 2
    assert len(memories_seen) == 2
    assert memories_seen[0].asked_question_ids == []
    assert len(memories_seen[1].asked_question_ids) == 1

    second_build_memory = area_builder.build.call_args_list[1].kwargs.get(
        "memory",
    )

    assert second_build_memory is not None
    assert len(second_build_memory.asked_question_ids) == 1
