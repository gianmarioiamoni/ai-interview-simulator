# tests/services/question_corpus/test_corpus_id_deduplicator.py

from domain.contracts.corpus.curated_question import CuratedQuestion
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.dedup.corpus_id_deduplicator import CorpusIdDeduplicator


def _build_question(
    question_id: str,
    text: str,
) -> CuratedQuestion:

    return CuratedQuestion(
        id=question_id,
        question=text,
        role=RoleType.BACKEND_ENGINEER,
        seniority=SeniorityLevel.MID,
        area=InterviewArea.TECH_CASE_STUDY,
        domains=["system_design"],
        difficulty=3,
        source="test_source",
        quality_score=0.8,
        tags=[],
        expected_topics=[],
    )


def test_deduplicate_keeps_first_occurrence() -> None:

    deduplicator = CorpusIdDeduplicator()

    questions = [
        _build_question("abc123", "First question text here."),
        _build_question("abc123", "Duplicate id different text."),
        _build_question("def456", "Second unique question here."),
    ]

    deduplicated, skipped = deduplicator.deduplicate(questions)

    assert skipped == 1
    assert len(deduplicated) == 2
    assert deduplicated[0].question == "First question text here."
    assert deduplicated[1].id == "def456"


def test_deduplicate_returns_all_when_unique() -> None:

    deduplicator = CorpusIdDeduplicator()

    questions = [
        _build_question("id_one", "Unique question number one."),
        _build_question("id_two", "Unique question number two."),
    ]

    deduplicated, skipped = deduplicator.deduplicate(questions)

    assert skipped == 0
    assert len(deduplicated) == 2
