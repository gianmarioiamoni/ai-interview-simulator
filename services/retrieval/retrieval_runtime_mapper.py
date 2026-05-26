# services/retrieval/retrieval_runtime_mapper.py

from datetime import datetime, timezone

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import (
    Role,
    RoleType,
)
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance

from services.retrieval.contracts import RetrievalCorpusRecord
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


class RetrievalRuntimeMapper:

    # =====================================================
    # PUBLIC
    # =====================================================

    def map(
        self,
        records: list[RetrievalCorpusRecord],
    ) -> list[QuestionBankItem]:

        return [self._map_record(record) for record in records]

    # =====================================================
    # INTERNALS
    # =====================================================

    def _map_record(
        self,
        record: RetrievalCorpusRecord,
    ) -> QuestionBankItem:

        category = (
            record.semantic_categories[0] if (record.semantic_categories) else "backend"
        )

        area = self._map_area(category)

        role = self._map_role(category)

        difficulty = max(
            1,
            min(
                5,
                int(record.retrieval_score * 10),
            ),
        )

        ingestion_metadata = IngestionMetadata(
            source_name="retrieval_runtime",
            source_type="retrieval",
            dataset_version="runtime_v1",
            ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        provenance = QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="retrieval_runtime",
            source_type="semantic_retrieval",
            dataset_version="runtime_v1",
            retrieval_score=record.retrieval_score,
        )


        return QuestionBankItem(
            id=(f"retrieval_" f"{abs(hash(record.content))}"),
            text=record.content,
            role=role,
            area=area,
            level=(SeniorityLevel.MID),
            difficulty=difficulty,
            interview_type="technical",
            ingestion_metadata=ingestion_metadata,
            provenance=provenance,
        )

    def _map_area(
        self,
        category: str,
    ) -> InterviewArea:

        mapping = {
            "distributed_systems": InterviewArea.TECH_CASE_STUDY,
            "database": InterviewArea.TECH_DATABASE,
            "data_engineering": InterviewArea.TECH_DATABASE,
            "devops": InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            "computer_science": InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            "backend": InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            "frontend": InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        }

        return mapping.get(
            category,
            InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        )

    def _map_role(
        self,
        category: str,
    ) -> Role:

        role_mapping = {
            "devops": RoleType.DEVOPS_ENGINEER,
            "data_engineering": RoleType.DATA_ENGINEER,
        }

        role_type = role_mapping.get(
            category,
            RoleType.BACKEND_ENGINEER,
        )

        return Role(type=role_type)
