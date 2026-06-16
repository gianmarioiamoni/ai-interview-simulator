# services/question_ingestion/mappers/curated_question_mapper.py

import hashlib

from domain.contracts.corpus.curated_question import CuratedQuestion
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_ingestion.contracts.normalized_question_record import (
    NormalizedQuestionRecord,
)
from services.question_ingestion.contracts.question_metadata import QuestionMetadata


PHASE_4A_QUALITY_SCORE = 0.80

DEFAULT_DIFFICULTY = 3


class CuratedQuestionMappingError(ValueError):
    pass


class CuratedQuestionMapper:

    # =====================================================
    # PUBLIC
    # =====================================================

    def map(
        self,
        record: NormalizedQuestionRecord,
        metadata: QuestionMetadata,
    ) -> CuratedQuestion:

        question_text = record.text.strip()

        if not question_text:
            raise CuratedQuestionMappingError("Question text is empty.")

        area = metadata.area

        if area is None:
            raise CuratedQuestionMappingError("Area metadata is required.")

        role = metadata.role or RoleType.FULLSTACK_ENGINEER

        seniority = metadata.level or SeniorityLevel.MID

        difficulty = metadata.difficulty if metadata.difficulty is not None else DEFAULT_DIFFICULTY

        source = record.source or record.ingestion_metadata.source_name

        return CuratedQuestion(
            id=self._generate_deterministic_id(question_text),
            question=question_text,
            role=role,
            seniority=seniority,
            area=area,
            domains=metadata.domains if metadata.domains else [area.value],
            difficulty=difficulty,
            source=source,
            quality_score=PHASE_4A_QUALITY_SCORE,
            tags=[],
            expected_topics=[],
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _generate_deterministic_id(
        self,
        question_text: str,
    ) -> str:

        normalized = question_text.strip().lower()

        digest = hashlib.sha256(
            normalized.encode("utf-8"),
        ).hexdigest()

        return digest[:16]
