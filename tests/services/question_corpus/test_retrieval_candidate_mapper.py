# tests/services/question_corpus/test_retrieval_candidate_mapper.py

import pytest
from langchain_core.documents import Document

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    CORPUS_INDEX_DATASET_VERSION,
    CorpusCandidateMappingError,
    RetrievalCandidateMapper,
    UNAVAILABLE_INDEX_INGESTION_TIMESTAMP_SENTINEL,
)


def _build_candidate(
    metadata_overrides: dict | None = None,
    page_content: str = "How would you design a distributed cache?",
) -> RetrievalCandidate:
    metadata = {
        "document_id": "backend_cache_001",
        "role": "backend_engineer",
        "area": "technical_case_study",
        "seniority": "senior",
        "difficulty": 5,
        "source": "manual_seed",
    }

    if metadata_overrides:
        metadata.update(metadata_overrides)

    return RetrievalCandidate(
        document=Document(
            page_content=page_content,
            metadata=metadata,
        ),
        semantic_score=0.85,
        quality_score=0.9,
        final_score=0.88,
        adaptive_score=0.91,
    )


def test_map_one_happy_path_maps_using_document_metadata() -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate()

    item = mapper.map_one(candidate)

    assert item.id == "backend_cache_001"
    assert item.text == "How would you design a distributed cache?"
    assert item.role.type == RoleType.BACKEND_ENGINEER
    assert item.area == InterviewArea.TECH_CASE_STUDY
    assert item.level == SeniorityLevel.SENIOR
    assert item.difficulty == 5
    assert item.provenance is not None
    assert item.provenance.origin_type == QuestionOriginType.RETRIEVAL
    assert item.provenance.source_type == "question_corpus"
    assert item.provenance.retrieval_score == 0.91
    assert (
        item.ingestion_metadata.ingestion_timestamp
        == UNAVAILABLE_INDEX_INGESTION_TIMESTAMP_SENTINEL
    )
    assert item.ingestion_metadata.dataset_version == CORPUS_INDEX_DATASET_VERSION


def test_map_uses_final_score_when_adaptive_score_missing() -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate()
    candidate = candidate.model_copy(update={"adaptive_score": None, "final_score": 0.77})

    item = mapper.map_one(candidate)

    assert item.provenance is not None
    assert item.provenance.retrieval_score == 0.77


def test_map_list_preserves_order_and_length() -> None:
    mapper = RetrievalCandidateMapper()
    first = _build_candidate({"document_id": "a"})
    second = _build_candidate({"document_id": "b"})

    items = mapper.map([first, second])

    assert len(items) == 2
    assert items[0].id == "a"
    assert items[1].id == "b"


@pytest.mark.parametrize(
    "missing_key",
    [
        "document_id",
        "role",
        "area",
        "seniority",
        "difficulty",
    ],
)
def test_map_one_fails_fast_when_required_metadata_missing(missing_key: str) -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate()
    metadata = dict(candidate.document.metadata)
    metadata.pop(missing_key)
    candidate = candidate.model_copy(
        update={
            "document": Document(
                page_content=candidate.document.page_content,
                metadata=metadata,
            )
        }
    )

    with pytest.raises(CorpusCandidateMappingError):
        mapper.map_one(candidate)


def test_map_one_fails_when_page_content_is_empty() -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate(page_content="   ")

    with pytest.raises(CorpusCandidateMappingError):
        mapper.map_one(candidate)


def test_map_one_fails_when_difficulty_is_not_numeric() -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate(metadata_overrides={"difficulty": "not-a-number"})

    with pytest.raises(CorpusCandidateMappingError):
        mapper.map_one(candidate)


def test_map_one_raises_for_unknown_role() -> None:
    """map_one must raise CorpusCandidateMappingError for any unknown role value."""
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate(metadata_overrides={"role": "invalid_role"})

    with pytest.raises(CorpusCandidateMappingError, match="Invalid corpus role value"):
        mapper.map_one(candidate)


def test_map_one_raises_for_role_other() -> None:
    """role='other' is not a valid corpus role; map_one must raise."""
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate(metadata_overrides={"role": "other"})

    with pytest.raises(CorpusCandidateMappingError, match="Invalid corpus role value"):
        mapper.map_one(candidate)


def test_map_skips_invalid_document_and_returns_valid_ones() -> None:
    """map() must silently skip documents that fail mapping and return the rest."""
    mapper = RetrievalCandidateMapper()
    good = _build_candidate({"document_id": "good"})
    bad_empty = _build_candidate({"document_id": "bad"}, page_content="   ")

    items = mapper.map([good, bad_empty])

    assert len(items) == 1
    assert items[0].id == "good"


def test_map_skips_doc_with_role_other_and_returns_valid_ones() -> None:
    """map() must skip role='other' docs without aborting; valid docs are returned."""
    mapper = RetrievalCandidateMapper()
    good = _build_candidate({"document_id": "good"})
    role_other = _build_candidate({"document_id": "bad_role", "role": "other"})

    items = mapper.map([role_other, good])

    assert len(items) == 1
    assert items[0].id == "good"


def test_map_returns_empty_list_when_all_documents_invalid() -> None:
    """map() must return [] (not raise) when every document fails mapping."""
    mapper = RetrievalCandidateMapper()
    bad1 = _build_candidate(page_content="   ")
    bad2 = _build_candidate({"area": "not_an_area"})

    items = mapper.map([bad1, bad2])

    assert items == []


def test_map_one_fails_when_area_is_invalid() -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate(metadata_overrides={"area": "invalid_area"})

    with pytest.raises(CorpusCandidateMappingError):
        mapper.map_one(candidate)


def test_map_one_fails_when_seniority_is_invalid() -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate(metadata_overrides={"seniority": "invalid_seniority"})

    with pytest.raises(CorpusCandidateMappingError):
        mapper.map_one(candidate)


def test_map_one_strips_legacy_metadata_lines_from_page_content() -> None:
    mapper = RetrievalCandidateMapper()

    legacy_page_content = (
        "Explain CAP theorem.\n"
        "Role: fullstack_engineer\n"
        "Area: technical_technical_knowledge\n"
        "Seniority: mid\n"
        "Domains: technical_technical_knowledge\n"
        "Topics: \n"
    )

    candidate = _build_candidate(page_content=legacy_page_content)

    item = mapper.map_one(candidate)

    assert item.text == "Explain CAP theorem."


def test_map_one_leaves_clean_page_content_unchanged() -> None:
    mapper = RetrievalCandidateMapper()
    candidate = _build_candidate(
        page_content="How would you design a distributed cache?",
    )

    item = mapper.map_one(candidate)

    assert item.text == "How would you design a distributed cache?"
