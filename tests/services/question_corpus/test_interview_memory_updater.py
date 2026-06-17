# tests/services/question_corpus/test_interview_memory_updater.py

import uuid

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
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


def _build_bank_item(
    question_id: str,
    domains: list[str] | None = None,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=question_id,
        text="How would you design a scalable cache?",
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_CASE_STUDY,
        level=SeniorityLevel.SENIOR,
        difficulty=4,
        domains=domains if domains is not None else [],
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


def _build_question(
    domains: list[str] | None = None,
    score: float = 0.7,
) -> Question:
    provenance = QuestionProvenance(
        origin_type=QuestionOriginType.RETRIEVAL,
        source_name="test",
        domains=domains if domains is not None else [],
    )
    return Question(
        id=str(uuid.uuid4()),
        area=InterviewArea.TECH_DATABASE,
        type=QuestionType.WRITTEN,
        prompt="Write a join query.",
        difficulty=QuestionDifficulty.MEDIUM,
        provenance=provenance,
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


def test_record_bank_item_selection_uses_item_domains_when_present() -> None:
    updater = InterviewMemoryUpdater()
    memory = InterviewRetrievalMemory()

    updated = updater.record_bank_item_selection(
        memory=memory,
        item=_build_bank_item("q1", domains=["join", "group_by"]),
    )

    assert "join" in updated.covered_domains
    assert "group_by" in updated.covered_domains
    assert "technical_case_study" not in updated.covered_domains


def test_record_bank_item_selection_falls_back_to_area_when_domains_empty() -> None:
    updater = InterviewMemoryUpdater()
    memory = InterviewRetrievalMemory()

    updated = updater.record_bank_item_selection(
        memory=memory,
        item=_build_bank_item("q2", domains=[]),
    )

    assert "technical_case_study" in updated.covered_domains


def test_update_from_question_evaluation_uses_provenance_domains() -> None:
    updater = InterviewMemoryUpdater()
    memory = InterviewRetrievalMemory()

    updated = updater.update_from_question_evaluation(
        memory=memory,
        question=_build_question(domains=["exists"]),
        evaluation_score=0.9,
    )

    assert "exists" in updated.covered_domains
    assert "technical_database" not in updated.covered_domains


def test_update_from_question_evaluation_falls_back_to_area_when_no_provenance_domains() -> None:
    updater = InterviewMemoryUpdater()
    memory = InterviewRetrievalMemory()

    q = _build_question(domains=[])

    updated = updater.update_from_question_evaluation(
        memory=memory,
        question=q,
        evaluation_score=0.5,
    )

    assert "technical_database" in updated.covered_domains


def test_update_from_question_evaluation_falls_back_to_area_when_no_provenance() -> None:
    updater = InterviewMemoryUpdater()
    memory = InterviewRetrievalMemory()

    q = Question(
        id=str(uuid.uuid4()),
        area=InterviewArea.TECH_DATABASE,
        type=QuestionType.WRITTEN,
        prompt="Explain indexing.",
        difficulty=QuestionDifficulty.EASY,
        provenance=None,
    )

    updated = updater.update_from_question_evaluation(
        memory=memory,
        question=q,
        evaluation_score=0.4,
    )

    assert "technical_database" in updated.covered_domains
