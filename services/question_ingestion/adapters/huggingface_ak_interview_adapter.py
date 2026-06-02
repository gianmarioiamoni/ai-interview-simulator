# services/question_ingestion/adapters/huggingface_ak_interview_adapter.py

import re

from services.question_ingestion.adapters.huggingface_dataset_adapter import (
    HuggingFaceDatasetAdapter,
)
from services.question_ingestion.contracts import RawQuestionRecord


AK_INTERVIEW_ROLE = "fullstack_engineer"

AREA_TECHNICAL_DATABASE = "technical_database"
AREA_TECHNICAL_CODING = "technical_coding"
AREA_HR_SITUATIONAL = "hr_situational"
AREA_TECHNICAL_KNOWLEDGE = "technical_technical_knowledge"

LEVEL_MID = "mid"
LEVEL_JUNIOR = "junior"

_QUESTION_ANSWER_PATTERN = re.compile(
    r"^Question:\s*(.*?)\s*Answer:",
    re.DOTALL,
)

_HR_KEYWORDS = (
    "strengths",
    "weaknesses",
    "achievement",
    "why do you want",
    "five years",
    "conflict",
    "teamwork",
)

_DATABASE_KEYWORDS = (
    "sql",
    "database",
    "normalization",
    "join",
    "index",
    "query",
)

_CODING_KEYWORDS = (
    "binary search",
    "algorithm",
    "linked list",
    "recursion",
    "stack",
    "queue",
    "dfs",
    "bfs",
    "dynamic programming",
)


class HuggingFaceAkInterviewAdapter(HuggingFaceDatasetAdapter):

    AREA = AREA_TECHNICAL_KNOWLEDGE
    ROLE = AK_INTERVIEW_ROLE
    LEVEL = LEVEL_JUNIOR

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt(
        self,
        payload: dict,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> RawQuestionRecord:

        question = self._extract_question(
            payload,
        )

        area = self._resolve_area(
            question,
        )

        level = self._resolve_level(
            question,
        )

        canonical_payload = {
            "text": question,
            "area": area,
            "role": AK_INTERVIEW_ROLE,
            "level": level,
        }

        return RawQuestionRecord(
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
            canonical_payload=canonical_payload,
            raw_payload=payload,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _extract_question(
        self,
        payload: dict,
    ) -> str:

        text = payload.get("text", "")

        if not isinstance(text, str):
            text = str(text)

        text = text.strip()

        match = _QUESTION_ANSWER_PATTERN.match(
            text,
        )

        if match is None:
            return text

        return match.group(1).strip()

    def _resolve_area(
        self,
        question: str,
    ) -> str:

        lower = question.lower()

        if any(keyword in lower for keyword in _HR_KEYWORDS):
            return AREA_HR_SITUATIONAL

        if any(keyword in lower for keyword in _DATABASE_KEYWORDS):
            return AREA_TECHNICAL_DATABASE

        if any(keyword in lower for keyword in _CODING_KEYWORDS):
            return AREA_TECHNICAL_CODING

        return AREA_TECHNICAL_KNOWLEDGE

    def _resolve_level(
        self,
        question: str,
    ) -> str:

        lower = question.lower()

        if any(keyword in lower for keyword in _HR_KEYWORDS):
            return LEVEL_MID

        if self._is_definition_style(
            lower,
        ):
            return LEVEL_JUNIOR

        return LEVEL_JUNIOR

    def _is_definition_style(
        self,
        lower: str,
    ) -> bool:

        return (
            lower.startswith("what is")
            or lower.startswith("explain")
            or lower.startswith("difference between")
            or lower.startswith("describe")
        )
