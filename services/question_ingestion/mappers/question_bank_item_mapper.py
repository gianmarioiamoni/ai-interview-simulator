# services/question_ingestion/mappers/question_bank_item_mapper.py

import uuid

from typing import List

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from services.question_ingestion.contracts import NormalizedQuestionRecord


class QuestionBankItemMapper:

    # =====================================================
    # PUBLIC
    # =====================================================

    def map(
        self,
        records: List[NormalizedQuestionRecord],
    ) -> List[QuestionBankItem]:

        items: List[QuestionBankItem] = []

        for record in records:

            item = self._map_record(record)

            if item is not None:
                items.append(item)

        return items

    # =====================================================
    # INTERNALS
    # =====================================================

    def _map_record(
        self,
        record: NormalizedQuestionRecord,
    ) -> QuestionBankItem | None:

        # -------------------------------------------------
        # REQUIRED METADATA
        # -------------------------------------------------

        if record.area_hint is None:
            return None

        if record.level_hint is None:
            return None

        # -------------------------------------------------
        # ROLE
        # -------------------------------------------------

        role_type = self._map_role(
            record.role_hint,
        )

        # -------------------------------------------------
        # AREA
        # -------------------------------------------------

        area = InterviewArea(
            record.area_hint,
        )

        # -------------------------------------------------
        # LEVEL
        # -------------------------------------------------

        level = SeniorityLevel(
            record.level_hint,
        )

        # -------------------------------------------------
        # DIFFICULTY
        # -------------------------------------------------

        difficulty = record.difficulty_hint or 3

        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name=record.ingestion_metadata.source_name,
            source_type=record.ingestion_metadata.source_type,
            dataset_version=record.ingestion_metadata.dataset_version,
        )

        # -------------------------------------------------
        # BUILD
        # -------------------------------------------------

        return QuestionBankItem(
            id=str(uuid.uuid4()),
            text=record.text,
            interview_type=InterviewType.TECHNICAL,
            role=Role(type=role_type),
            area=area,
            level=level,
            difficulty=difficulty,
            ingestion_metadata=record.ingestion_metadata,
            provenance=provenance,
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _map_role(
        self,
        role_hint: str | None,
    ) -> RoleType:

        if role_hint is None:
            return RoleType.FULLSTACK_ENGINEER

        return RoleType(role_hint)
