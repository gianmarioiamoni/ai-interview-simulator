# services/interview_reasoner/context_builder_errors.py
"""Dedicated exceptions raised by ReasoningContextBuilder (ADR-038)."""


class ContextBuilderError(Exception):
    """Base class for all ReasoningContextBuilder errors."""


class MissingInterviewMemoryError(ContextBuilderError):
    """Raised when InterviewState.interview_memory is absent or uninitialized."""

    def __init__(self) -> None:
        super().__init__(
            "InterviewState.interview_memory is required but was not found."
        )


class IncoherentQuestionHistoryError(ContextBuilderError):
    """Raised when asked_question_ids and questions lists are inconsistent."""

    def __init__(self, asked: int, available: int) -> None:
        super().__init__(
            f"asked_question_ids references {asked} question(s) "
            f"but only {available} question(s) are available."
        )
        self.asked = asked
        self.available = available


class InvalidEvidenceStoreError(ContextBuilderError):
    """Raised when EvidenceStore inside InterviewMemory is in an invalid state."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"EvidenceStore is invalid: {reason}")
        self.reason = reason
