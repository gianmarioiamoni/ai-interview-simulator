# services/question_ingestion/adapters/leetcode_question_groups_adapter.py

import json

from pathlib import Path

from services.question_ingestion.contracts import RawQuestionRecord

CODING_AREA = "technical_coding"
CODING_ROLE = "fullstack_engineer"

DIFFICULTY_TO_LEVEL = {
    "Easy": "junior",
    "Medium": "mid",
    "Hard": "senior",
}

DIFFICULTY_TO_SCORE = {
    "Easy": 2,
    "Medium": 3,
    "Hard": 4,
}

DEFAULT_LEVEL = "mid"
DEFAULT_DIFFICULTY = 3


class LeetcodeQuestionGroupsAdapter:

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt_file(
        self,
        dataset_path: str,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> list[RawQuestionRecord]:

        path = Path(dataset_path)

        payload = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError("QuestionGroups root must be a JSON object")

        return self.adapt_document(
            payload=payload,
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
        )

    def adapt_document(
        self,
        payload: dict,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> list[RawQuestionRecord]:

        records: list[RawQuestionRecord] = []
        seen_slugs: set[str] = set()

        for entries in payload.values():

            if not isinstance(
                entries,
                list,
            ):
                continue

            for entry in entries:

                if not isinstance(
                    entry,
                    dict,
                ):
                    continue

                slug = entry.get(
                    "slug",
                )

                if not isinstance(
                    slug,
                    str,
                ) or not slug.strip():
                    continue

                normalized_slug = slug.strip().lower()

                if normalized_slug in seen_slugs:
                    continue

                seen_slugs.add(
                    normalized_slug,
                )

                records.append(
                    self.adapt(
                        payload=entry,
                        source=source,
                        source_type=source_type,
                        dataset_version=dataset_version,
                    )
                )

        return records

    def adapt(
        self,
        payload: dict,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> RawQuestionRecord:

        title = payload.get(
            "title",
            "",
        )

        if not isinstance(
            title,
            str,
        ):
            title = str(title)

        title = title.strip()

        question = self._format_question(
            title,
        )

        difficulty_label = payload.get(
            "difficulty",
        )

        level = self._resolve_level(
            difficulty_label,
        )

        difficulty = self._resolve_difficulty(
            difficulty_label,
        )

        canonical_payload = {
            "text": question,
            "area": CODING_AREA,
            "role": CODING_ROLE,
            "level": level,
            "difficulty": difficulty,
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

    def _format_question(
        self,
        title: str,
    ) -> str:

        return f"How would you solve {title}?"

    def _resolve_level(
        self,
        difficulty_label: str | None,
    ) -> str:

        if not isinstance(
            difficulty_label,
            str,
        ):
            return DEFAULT_LEVEL

        return DIFFICULTY_TO_LEVEL.get(
            difficulty_label,
            DEFAULT_LEVEL,
        )

    def _resolve_difficulty(
        self,
        difficulty_label: str | None,
    ) -> int:

        if not isinstance(
            difficulty_label,
            str,
        ):
            return DEFAULT_DIFFICULTY

        return DIFFICULTY_TO_SCORE.get(
            difficulty_label,
            DEFAULT_DIFFICULTY,
        )
