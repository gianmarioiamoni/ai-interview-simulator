# services/question_ingestion/adapters/behavioral_markdown_adapter.py

import re

from services.question_ingestion.contracts import RawQuestionRecord

BEHAVIORAL_ROLE = "fullstack_engineer"
BEHAVIORAL_LEVEL = "mid"

AREA_HR_BACKGROUND = "hr_background"
AREA_HR_SITUATIONAL = "hr_situational"
AREA_HR_BRAIN_TEASER = "hr_brain_teaser"
AREA_HR_ANALYTICAL = "hr_analytical"
AREA_HR_TECHNICAL_KNOWLEDGE = "hr_technical_knowledge"

_MIN_QUESTION_LENGTH = 15
_MAX_QUESTION_LENGTH = 400

_LIST_ITEM_PATTERN = re.compile(
    r"^\s*(?:\d+\.|[-*])\s+(.+)$",
)

_MARKDOWN_EMPHASIS_PATTERN = re.compile(
    r"\*\*([^*]+)\*\*|_([^_]+)_",
)

_QUESTION_SIGNAL_PATTERN = re.compile(
    r"\?|^Tell me|^Why |^What |^How |^Describe|^Explain|^Talk about|^Share |^Give me|^Imagine|^Name a|^If you|^Where do you",
    re.IGNORECASE,
)

_HR_AREA_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        AREA_HR_BRAIN_TEASER,
        (
            "unlimited budget",
            "gerbil",
            "90% of people disagree",
            "grandmother",
            "belong anywhere",
            "teach your interviewer",
            "something broken around you",
        ),
    ),
    (
        AREA_HR_ANALYTICAL,
        (
            "analytical problem",
            "priorit",
            "how would you improve",
            "how does ",
            "impact our",
        ),
    ),
    (
        AREA_HR_TECHNICAL_KNOWLEDGE,
        (
            "difficult bug",
            "hardest technical",
            "technical problem",
            "stay up to date with the latest technologies",
            "what have you built",
        ),
    ),
    (
        AREA_HR_SITUATIONAL,
        (
            "tell me about a time",
            "give an example",
            "describe a time",
            "situation where",
            "conflict with",
            "disagreement",
            "deadline",
            "failed",
            "overcame",
            "uncomfortable",
            "terrible news",
            "overwhelming",
            "not responsive",
            "difference of opinion",
            "tackle challenges",
        ),
    ),
    (
        AREA_HR_BACKGROUND,
        (
            "why do you want",
            "why do you like",
            "why lyft",
            "why amazon",
            "why slack",
            "why airbnb",
            "looking for in your next",
            "leave your current",
            "tell me about yourself",
            "strength",
            "weakness",
            "five years",
            "5 years",
            "salary",
            "motivat",
            "passionate",
            "fit for",
            "colleagues use to describe",
            "manager say",
            "hope to achieve",
            "first six months",
            "excited about",
            "mission resonates",
            "human resources means",
        ),
    ),
)


class BehavioralMarkdownAdapter:

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt_document(
        self,
        content: str,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> list[RawQuestionRecord]:

        questions = self._extract_questions(
            content,
        )

        return [
            self.adapt(
                payload={
                    "text": question,
                },
                source=source,
                source_type=source_type,
                dataset_version=dataset_version,
            )
            for question in questions
        ]

    def adapt(
        self,
        payload: dict,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> RawQuestionRecord:

        question = payload.get(
            "text",
            "",
        )

        if not isinstance(
            question,
            str,
        ):
            question = str(question)

        question = question.strip()

        area = self._resolve_area(
            question,
        )

        canonical_payload = {
            "text": question,
            "area": area,
            "role": BEHAVIORAL_ROLE,
            "level": BEHAVIORAL_LEVEL,
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

    def _extract_questions(
        self,
        content: str,
    ) -> list[str]:

        candidates: list[str] = []

        for line in content.splitlines():

            match = _LIST_ITEM_PATTERN.match(
                line.strip(),
            )

            if match is None:
                continue

            text = self._clean_markdown(
                match.group(1).strip(),
            )

            if not self._is_question_candidate(
                text,
            ):
                continue

            candidates.append(
                text,
            )

        return self._deduplicate(
            candidates,
        )

    def _clean_markdown(
        self,
        text: str,
    ) -> str:

        return _MARKDOWN_EMPHASIS_PATTERN.sub(
            r"\1\2",
            text,
        ).strip()

    def _is_question_candidate(
        self,
        text: str,
    ) -> bool:

        if len(text) < _MIN_QUESTION_LENGTH:
            return False

        if len(text) > _MAX_QUESTION_LENGTH:
            return False

        if text.startswith(
            (
                "Junior:",
                "Senior:",
                "Staff:",
            )
        ):
            return False

        return _QUESTION_SIGNAL_PATTERN.search(
            text,
        ) is not None

    def _deduplicate(
        self,
        questions: list[str],
    ) -> list[str]:

        seen: set[str] = set()
        unique: list[str] = []

        for question in questions:

            key = question.strip().lower()

            if key in seen:
                continue

            seen.add(key)
            unique.append(question)

        return unique

    def _resolve_area(
        self,
        question: str,
    ) -> str:

        lower = question.lower()

        for area, keywords in _HR_AREA_RULES:

            if any(
                keyword in lower
                for keyword in keywords
            ):
                return area

        return AREA_HR_SITUATIONAL
