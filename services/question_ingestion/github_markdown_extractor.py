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

        return questions

    # =====================================================
    # HELPERS
    # =====================================================

    def _clean_line(
        self,
        line: str,
    ) -> str:

        cleaned = line.strip()

        cleaned = re.sub(
            r"^[-*#>\d.\s]+",
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

        question_starters = [
            "how",
            "what",
            "why",
            "when",
            "where",
            "explain",
            "describe",
            "design",
            "implement",
        ]

        normalized = text.lower()

        return any(normalized.startswith(starter) for starter in (question_starters))
