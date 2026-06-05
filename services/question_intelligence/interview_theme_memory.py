# services/question_intelligence/interview_theme_memory.py

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

THEME_ANCHOR_PREFIX = "theme_anchor:"


def get_interview_theme_anchor(
    memory: InterviewRetrievalMemory,
) -> str | None:

    for domain in memory.strong_domains:

        if domain.startswith(THEME_ANCHOR_PREFIX):
            return domain[len(THEME_ANCHOR_PREFIX) :]

    return None


def with_interview_theme_anchor(
    memory: InterviewRetrievalMemory,
    theme_anchor: str,
) -> InterviewRetrievalMemory:

    preserved = [
        domain
        for domain in memory.strong_domains
        if not domain.startswith(THEME_ANCHOR_PREFIX)
    ]

    anchored = [f"{THEME_ANCHOR_PREFIX}{theme_anchor}"] + preserved

    return memory.model_copy(
        update={"strong_domains": anchored},
    )
