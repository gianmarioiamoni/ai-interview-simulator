# services/question_corpus/mappers/curated_question_bank_item_mapper.py

from datetime import datetime, timezone

from domain.contracts.corpus.curated_question import CuratedQuestion
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata

CORPUS_MERGE_AUDIT_DATASET_VERSION = "corpus_merge_audit"

UNAVAILABLE_MERGE_AUDIT_INGESTION_TIMESTAMP = datetime(
    1970,
    1,
    1,
    tzinfo=timezone.utc,
)


class CuratedQuestionBankItemMapper:

    # =====================================================
    # PUBLIC
    # =====================================================

    def map(
        self,
        questions: list[CuratedQuestion],
    ) -> list[QuestionBankItem]:

        return [self.map_one(question) for question in questions]

    def map_one(
        self,
        question: CuratedQuestion,
    ) -> QuestionBankItem:

        ingestion_metadata = IngestionMetadata(
            source_name=question.source,
            source_type="curated_json",
            dataset_version=CORPUS_MERGE_AUDIT_DATASET_VERSION,
            ingestion_timestamp=UNAVAILABLE_MERGE_AUDIT_INGESTION_TIMESTAMP,
        )

        provenance = QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name=question.source,
            source_type="curated_json",
            dataset_version=CORPUS_MERGE_AUDIT_DATASET_VERSION,
        )

        return QuestionBankItem(
            id=question.id,
            text=question.question,
            interview_type=InterviewType.TECHNICAL,
            role=Role(type=question.role),
            area=question.area,
            level=question.seniority,
            difficulty=question.difficulty,
            ingestion_metadata=ingestion_metadata,
            provenance=provenance,
        )
