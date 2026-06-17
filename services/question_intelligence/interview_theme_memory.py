# services/question_intelligence/interview_theme_memory.py

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

THEME_ANCHOR_PREFIX = "theme_anchor:"


def get_interview_theme_anchor(
    memory: InterviewRetrievalMemory,
) -> str | None:
    return memory.theme_anchor


def with_interview_theme_anchor(
    memory: InterviewRetrievalMemory,
    theme_anchor: str,
) -> InterviewRetrievalMemory:
    return memory.model_copy(
        update={"theme_anchor": theme_anchor},
    )
