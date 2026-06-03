# tests/services/question_intelligence/test_written_provenance_pipeline.py

from unittest.mock import MagicMock

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.pipelines.written_question_pipeline import (
    WrittenQuestionPipeline,
)
from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


CORPUS_SOURCE = "seed_questions"
RETRIEVAL_SCORE = 0.87


def _build_bank_item() -> QuestionBankItem:

    return QuestionBankItem(
        id="ca52309c655be942",
        text="Explain CAP theorem.",
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.FULLSTACK_ENGINEER),
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        level=SeniorityLevel.MID,
        difficulty=2,
        ingestion_metadata=IngestionMetadata(
            source_name=CORPUS_SOURCE,
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp="2020-01-01T00:00:00Z",
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name=CORPUS_SOURCE,
            source_type="question_corpus",
            dataset_version="v1",
            retrieval_score=RETRIEVAL_SCORE,
        ),
    )


def test_written_pipeline_retrieved_question_preserves_provenance() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    retrieval_service.retrieve.return_value = [_build_bank_item()]

    generator = MagicMock(spec=QuestionGenerator)
    generator.generate.return_value = []

    pipeline = WrittenQuestionPipeline(
        retrieval_service=retrieval_service,
        generator=generator,
    )

    questions, _memory = pipeline.build(
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        questions_per_area=1,
        memory=InterviewRetrievalMemory(),
    )

    assert len(questions) == 1
    assert questions[0].type == QuestionType.WRITTEN
    assert questions[0].prompt == "Explain CAP theorem."
    assert questions[0].provenance is not None
    assert questions[0].provenance.origin_type == QuestionOriginType.RETRIEVAL
    assert questions[0].provenance.source_name == CORPUS_SOURCE
    assert questions[0].provenance.retrieval_score == RETRIEVAL_SCORE


def test_written_pipeline_generated_fallback_has_no_provenance() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    retrieval_service.retrieve.return_value = []

    from domain.contracts.question.generated_question import GeneratedQuestion

    generator = MagicMock(spec=QuestionGenerator)
    generator.generate.return_value = [
        GeneratedQuestion(
            text="Describe how you would scale a web application.",
            difficulty=3,
        ),
    ]

    pipeline = WrittenQuestionPipeline(
        retrieval_service=retrieval_service,
        generator=generator,
    )

    questions, _memory = pipeline.build(
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        questions_per_area=1,
    )

    assert len(questions) == 1
    assert questions[0].provenance is None
