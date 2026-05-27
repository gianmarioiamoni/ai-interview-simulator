# services/question_ingestion/github_markdown_extractor.py

import re

from services.question_ingestion.contracts import (
    GitHubDocument,
    ExtractedQuestionCandidate,
)


class GitHubMarkdownExtractor:

    # =====================================================
    # PUBLIC
    # =====================================================

    def extract_questions(
        self,
        document: GitHubDocument,
    ) -> list[ExtractedQuestionCandidate]:

        lines = document.content.splitlines()

        questions: list[ExtractedQuestionCandidate] = []

        current_section: str | None = None

        for index, line in enumerate(lines):

            stripped = line.strip()

            # -------------------------------------------------
            # SECTION TRACKING
            # -------------------------------------------------

            if self._is_section_header(stripped):

                current_section = self._clean_section_header(
                    stripped,
                )

                continue

            # -------------------------------------------------
            # CLEAN LINE
            # -------------------------------------------------

            cleaned = self._clean_line(stripped)

            if not cleaned:
                continue

            # -------------------------------------------------
            # QUESTION DETECTION
            # -------------------------------------------------

            if not self._is_question(cleaned):
                continue

            # -------------------------------------------------
            # CONTEXT ENRICHMENT
            # -------------------------------------------------

            enriched = self._enrich_question(
                question=cleaned,
                section_context=current_section,
            )

            questions.append(
                ExtractedQuestionCandidate(
                    text=enriched,
                    section_context=current_section,
                    repository_context=document.repository,
                    source_file=document.path,
                    line_number=index + 1,
                )
            )

        return self._deduplicate(
            questions,
        )

    # =====================================================
    # SECTION HELPERS
    # =====================================================

    def _is_section_header(
        self,
        line: str,
    ) -> bool:

        return bool(
            re.match(
                r"^#+\s+",
                line,
            )
        )

    def _clean_section_header(
        self,
        line: str,
    ) -> str:

        cleaned = re.sub(
            r"^#+\s*",
            "",
            line,
        )

        return cleaned.strip()

    # =====================================================
    # CLEANING
    # =====================================================

    def _clean_line(
        self,
        line: str,
    ) -> str:

        cleaned = line.strip()

        prefixes = [
            "- ",
            "* ",
            "> ",
        ]

        for prefix in prefixes:

            if cleaned.startswith(prefix):

                cleaned = cleaned[len(prefix) :]

        cleaned = re.sub(
            r"^\d+\.\s*",
            "",
            cleaned,
        )

        return cleaned.strip()

    # =====================================================
    # QUESTION DETECTION
    # =====================================================

    def _is_question(
        self,
        text: str,
    ) -> bool:

        if len(text) < 15:
            return False

        patterns = [
            r"\?$",
            r"^Explain\s",
            r"^Describe\s",
            r"^How\s",
            r"^What\s",
            r"^Why\s",
            r"^When\s",
            r"^Where\s",
            r"^Design\s",
            r"^Implement\s",
        ]

        for pattern in patterns:

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                return True

        return False

    # =====================================================
    # CONTEXT ENRICHMENT
    # =====================================================

    def _enrich_question(
        self,
        question: str,
        section_context: str | None,
    ) -> str:

        normalized = question.strip()

        # -------------------------------------------------
        # CONTEXT-DEPENDENT FRAGMENTS
        # -------------------------------------------------

        weak_starts = [
            "when to",
            "when should",
            "what about",
            "how about",
        ]

        lowered = normalized.lower()

        is_weak = any(lowered.startswith(prefix) for prefix in weak_starts)

        if is_weak and section_context:

            return (
                f"In the context of {section_context}, "
                f"{normalized[0].lower() + normalized[1:]}"
            )

        return normalized

    # =====================================================
    # DEDUPLICATION
    # =====================================================

    def _deduplicate(
        self,
        questions: list[ExtractedQuestionCandidate],
    ) -> list[ExtractedQuestionCandidate]:

        seen: set[str] = set()

        unique: list[ExtractedQuestionCandidate] = []

        for question in questions:

            normalized = question.text.strip().lower()

            if normalized in seen:
                continue

            seen.add(normalized)

            unique.append(question)

        return unique
