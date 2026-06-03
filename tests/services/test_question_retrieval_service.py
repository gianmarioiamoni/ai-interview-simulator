# tests/services/test_question_retrieval_service.py

from unittest.mock import MagicMock

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    CORPUS_INDEX_DATASET_VERSION,
    UNAVAILABLE_INDEX_INGESTION_TIMESTAMP_SENTINEL,
)
from services.question_intelligence.question_retrieval_service import QuestionRetrievalService
from services.question_intelligence.retrieval.retrieval_strategy import RetrievalStrategy
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


def _sample_bank_item() -> QuestionBankItem:
    ingestion_metadata = IngestionMetadata(
        source_name="manual_seed",
        source_type="question_corpus",
        dataset_version=CORPUS_INDEX_DATASET_VERSION,
        ingestion_timestamp=UNAVAILABLE_INDEX_INGESTION_TIMESTAMP_SENTINEL,
    )

    return QuestionBankItem(
        id="q-runtime-1",
        text="Explain caching.",
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_CASE_STUDY,
        level=SeniorityLevel.MID,
        difficulty=3,
        ingestion_metadata=ingestion_metadata,
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="manual_seed",
            source_type="question_corpus",
            dataset_version=CORPUS_INDEX_DATASET_VERSION,
            retrieval_score=0.9,
        ),
    )


def test_retrieve_delegates_to_runtime_and_mapper() -> None:
    context_adapter = MagicMock()
    runtime = MagicMock()
    mapper = MagicMock()

    context = object()
    candidates = [object()]
    mapped = [_sample_bank_item()]

    context_adapter.adapt.return_value = context
    runtime.retrieve_questions.return_value = candidates
    mapper.map.return_value = mapped

    service = QuestionRetrievalService(
        vector_store=MagicMock(),
        context_adapter=context_adapter,
        question_retrieval_runtime=runtime,
        retrieval_candidate_mapper=mapper,
    )

    strategy = RetrievalStrategy(k=3, fetch_k=12, use_mmr=False)

    results = service.retrieve(
        query="distributed cache",
        retrieval_strategy=strategy,
        role="backend_engineer",
        level="mid",
        interview_type="technical",
        area="technical_case_study",
    )

    context_adapter.adapt.assert_called_once_with(
        query="distributed cache",
        retrieval_strategy=strategy,
        role="backend_engineer",
        level="mid",
        interview_type="technical",
        area="technical_case_study",
        memory=None,
    )
    runtime.retrieve_questions.assert_called_once_with(
        query="distributed cache",
        context=context,
    )
    mapper.map.assert_called_once_with(candidates=candidates)
    assert results == mapped


def test_retrieve_returns_list_of_question_bank_item() -> None:
    context_adapter = MagicMock()
    runtime = MagicMock()
    mapper = MagicMock()

    bank_item = _sample_bank_item()
    context_adapter.adapt.return_value = object()
    runtime.retrieve_questions.return_value = [object()]
    mapper.map.return_value = [bank_item]

    service = QuestionRetrievalService(
        context_adapter=context_adapter,
        question_retrieval_runtime=runtime,
        retrieval_candidate_mapper=mapper,
    )

    results = service.retrieve(
        query="system design",
        retrieval_strategy=RetrievalStrategy(k=5, fetch_k=20),
    )

    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], QuestionBankItem)