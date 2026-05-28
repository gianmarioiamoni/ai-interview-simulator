# services/question_ingestion/semantic_candidate_extractor.py

import re

from services.question_ingestion.contracts.markdown_section import MarkdownSection
from services.question_ingestion.contracts.candidate_question import CandidateQuestion


class SemanticCandidateExtractor:

    MIN_LENGTH = 20
    MAX_LENGTH = 400

    # =====================================================
    # PUBLIC
    # =====================================================

    def extract(
        self,
        sections: list[MarkdownSection],
    ) -> list[CandidateQuestion]:

        candidates: list[CandidateQuestion] = []

        for section in sections:

            extracted = self._extract_from_section(
                section,
            )

            candidates.extend(extracted)

        return self._deduplicate(candidates)

    # =====================================================
    # INTERNALS
    # =====================================================

    def _extract_from_section(
        self,
        section: MarkdownSection,
    ) -> list[CandidateQuestion]:

        candidates: list[CandidateQuestion] = []

        lines = section.content.splitlines()

        for line in lines:

            cleaned = self._clean(line)

            if not cleaned:
                continue

            if not self._is_candidate(cleaned):
                continue

            candidates.append(
                CandidateQuestion(
                    text=cleaned,
                    section_heading=section.heading,
                    source_file=section.source_path,
                    surrounding_context=section.content[:500],
                )
            )

        return candidates

    def _clean(
        self,
        text: str,
    ) -> str:

        cleaned = text.strip()

        cleaned = re.sub(
            r"^[-*+]\s*",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"^\d+\.\s*",
            "",
            cleaned,
        )

        return cleaned.strip()

    def _is_candidate(
        self,
        text: str,
    ) -> bool:

        if len(text) < self.MIN_LENGTH:
            return False

        if len(text) > self.MAX_LENGTH:
            return False

        # -------------------------------------------------
        # QUESTION SIGNALS
        # -------------------------------------------------

        patterns = [
            r"\?$",
            r"^How\s",
            r"^What\s",
            r"^Why\s",
            r"^Explain\s",
            r"^Design\s",
            r"^Implement\s",
            r"^Describe\s",
            r"^Compare\s",
        ]

        for pattern in patterns:

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                return True

        return False

    def _deduplicate(
        self,
        candidates: list[CandidateQuestion],
    ) -> list[CandidateQuestion]:

        seen: set[str] = set()

        unique: list[CandidateQuestion] = []

        for candidate in candidates:

            normalized = candidate.text.strip().lower()

            if normalized in seen:
                continue

            seen.add(normalized)

            unique.append(candidate)

        return unique
