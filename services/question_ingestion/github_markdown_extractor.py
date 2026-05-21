# services/question_ingestion/github_markdown_extractor.py

import re

from services.question_ingestion.contracts import (
    GitHubDocument,
)


class GitHubMarkdownExtractor:

    # =====================================================
    # PUBLIC
    # =====================================================

    def extract_questions(
        self,
        document: GitHubDocument,
    ) -> list[str]:

        lines = document.content.splitlines()

        questions: list[str] = []

        for line in lines:

            cleaned = self._clean_line(line)

            if not cleaned:
                continue

            if self._is_question(cleaned):
                questions.append(cleaned)

        return self._deduplicate(questions)

    # =====================================================
    # HELPERS
    # =====================================================

    def _clean_line(
        self,
        line: str,
    ) -> str:

        cleaned = line.strip()

        # -------------------------------------------------
        # REMOVE COMMON MARKDOWN PREFIXES
        # -------------------------------------------------

        prefixes = [
            "- ",
            "* ",
            "> ",
        ]

        for prefix in prefixes:

            if cleaned.startswith(prefix):

                cleaned = cleaned[len(prefix) :]

        # -------------------------------------------------
        # REMOVE HEADERS
        # -------------------------------------------------

        cleaned = re.sub(
            r"^#+\s*",
            "",
            cleaned,
        )

        # -------------------------------------------------
        # REMOVE ORDERED LIST PREFIXES
        # -------------------------------------------------

        cleaned = re.sub(
            r"^\d+\.\s*",
            "",
            cleaned,
        )

        return cleaned.strip()

    def _is_question(
        self,
        text: str,
    ) -> bool:

        if len(text) < 15:
            return False

        question_patterns = [
            # direct questions
            r"\?$",
            # explanation prompts
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

        for pattern in question_patterns:

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                return True

        return False

    def _deduplicate(
        self,
        questions: list[str],
    ) -> list[str]:

        seen: set[str] = set()

        unique_questions: list[str] = []

        for question in questions:

            normalized = question.strip().lower()

            if normalized in seen:
                continue

            seen.add(normalized)

            unique_questions.append(question)

        return unique_questions
