# tests/services/question_corpus/test_interview_memory_updater.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


def _build_bank_item(
    question_id: str,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=question_id,
        text="How would you design a scalable cache?",
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_CASE_STUDY,
        level=SeniorityLevel.SENIOR,
        difficulty=4,
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


def test_record_bank_item_selection_adds_id_and_domain() -> None:

    updater = InterviewMemoryUpdater()

    memory = InterviewRetrievalMemory()

    updated = updater.record_bank_item_selection(
        memory=memory,
        item=_build_bank_item("corpus_question_a"),
    )

    assert updated.asked_question_ids == ["corpus_question_a"]
    assert "technical_case_study" in updated.covered_domains
    assert updated.difficulty_history == [4]


def test_record_bank_item_selection_skips_duplicate_id() -> None:

    updater = InterviewMemoryUpdater()

    memory = InterviewRetrievalMemory(
        asked_question_ids=["corpus_question_a"],
    )

    updated = updater.record_bank_item_selection(
        memory=memory,
        item=_build_bank_item("corpus_question_a"),
    )

    assert updated == memory
