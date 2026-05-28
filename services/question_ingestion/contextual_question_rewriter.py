import re

from services.question_ingestion.contracts.candidate_question import CandidateQuestion
from services.question_ingestion.heading_semantic_classifier import HeadingSemanticClassifier


class ContextualQuestionRewriter:

    def __init__(self) -> None:
        self._heading_classifier = HeadingSemanticClassifier()

    # =====================================================
    # PUBLIC
    # =====================================================

    def rewrite(
        self,
        candidate: CandidateQuestion,
    ) -> str:

        if not self._heading_classifier.is_semantic(candidate.section_heading):
            return candidate.text

        text = candidate.text.strip()

        heading = candidate.section_heading.strip()

        if self._is_standalone(text):
            return text

        rewritten = self._rewrite_with_heading(
            heading=heading,
            text=text,
        )

        return rewritten

    # =====================================================
    # INTERNALS
    # =====================================================

    def _is_standalone(
        self,
        text: str,
    ) -> bool:

        standalone_patterns = [
            r"^how",
            r"^what",
            r"^why",
            r"^explain",
            r"^describe",
            r"^implement",
            r"^design",
        ]

        normalized = text.lower()

        return any(re.search(pattern, normalized) for pattern in standalone_patterns)

    def _rewrite_with_heading(
        self,
        heading: str,
        text: str,
    ) -> str:

        normalized = text.lower()

        if normalized.startswith("when to"):

            rewritten = re.sub(
                r"^when to",
                "When should",
                text,
                flags=re.IGNORECASE,
            )

            return f"[{heading}] {rewritten}"

        if normalized.startswith("how to"):

            rewritten = re.sub(
                r"^how to",
                "How would you",
                text,
                flags=re.IGNORECASE,
            )

            return f"[{heading}] {rewritten}"

        return f"[{heading}] {text}"
