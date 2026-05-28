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

            # -------------------------------------------------
            # HEADING-DERIVED PROMPT
            # -------------------------------------------------

            if not extracted:

                generated = self._generate_heading_prompt(
                    section.heading,
                )

                if generated:

                    candidates.append(
                        CandidateQuestion(
                            text=generated,
                            section_heading=section.heading,
                            source_file=section.source_path,
                            surrounding_context=section.content[:500],
                        )
                    )

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

            density = self._semantic_density(cleaned)

            if density < 0.03:
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

        question_patterns = [
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

        semantic_patterns = [
            r"trade[- ]?offs?",
            r"bottlenecks?",
            r"failure modes?",
            r"latency",
            r"throughput",
            r"replication",
            r"partitioning",
            r"consistency",
            r"scalability",
            r"distributed",
            r"architecture",
            r"cache",
            r"database",
        ]

        question_match = any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in question_patterns
        )

        if question_match:
            return True

        semantic_match = any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in semantic_patterns
        )

        return semantic_match

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

    def _generate_heading_prompt(
        self,
        heading: str,
    ) -> str | None:

        normalized = heading.strip()

        if len(normalized) < 4:
            return None

        return f"Explain {normalized}."

    def _semantic_density(
        self,
        text: str,
    ) -> float:

        technical_terms = [
            "cache",
            "database",
            "distributed",
            "replication",
            "latency",
            "consistency",
            "architecture",
            "api",
            "scaling",
            "system",
            "backend",
            "throughput",
        ]

        normalized = text.lower()

        matches = sum(1 for term in technical_terms if term in normalized)

        return matches / max(
            len(normalized.split()),
            1,
        )
