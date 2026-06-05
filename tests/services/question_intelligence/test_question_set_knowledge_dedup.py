# tests/services/question_intelligence/test_question_set_knowledge_dedup.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question, QuestionType
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from services.question_intelligence.question_set_knowledge_dedup import (
    is_corpus_backed_knowledge_question,
    prioritize_technical_knowledge_for_dedup,
)


def _corpus_knowledge_question(
    prompt: str = "Explain CAP theorem trade-offs.",
) -> Question:

    return Question(
        id="corpus-knowledge",
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        type=QuestionType.WRITTEN,
        prompt=prompt,
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
        ),
    )


def _fallback_knowledge_question(
    prompt: str = "Explain CAP theorem trade-offs.",
) -> Question:

    return Question(
        id="fallback-knowledge",
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        type=QuestionType.WRITTEN,
        prompt=prompt,
        provenance=None,
    )


def _background_question(
    prompt: str = "Explain CAP theorem trade-offs.",
) -> Question:

    return Question(
        id="background",
        area=InterviewArea.TECH_BACKGROUND,
        type=QuestionType.WRITTEN,
        prompt=prompt,
        provenance=None,
    )


def test_is_corpus_backed_knowledge_question() -> None:

    assert is_corpus_backed_knowledge_question(_corpus_knowledge_question()) is True
    assert is_corpus_backed_knowledge_question(_fallback_knowledge_question()) is False


def test_prioritize_technical_knowledge_for_dedup_orders_knowledge_first() -> None:

    background = _background_question()
    knowledge = _corpus_knowledge_question()
    ordered = prioritize_technical_knowledge_for_dedup([background, knowledge])

    assert ordered.index(knowledge) < ordered.index(background)


def test_prioritize_technical_knowledge_orders_corpus_before_fallback() -> None:

    fallback = _fallback_knowledge_question()
    corpus = _corpus_knowledge_question()
    ordered = prioritize_technical_knowledge_for_dedup([fallback, corpus])

    assert ordered.index(corpus) < ordered.index(fallback)


def test_dedup_retains_knowledge_over_competing_area() -> None:

    background = _background_question()
    knowledge = _corpus_knowledge_question()

    without_priority = [background, knowledge]
    with_priority = prioritize_technical_knowledge_for_dedup(without_priority)

    def keep_first_only(questions: list[Question]) -> list[Question]:
        return [questions[0]] if questions else []

    kept_without = keep_first_only(without_priority)
    kept_with = keep_first_only(with_priority)

    assert kept_without[0].area == InterviewArea.TECH_BACKGROUND
    assert kept_with[0].area == InterviewArea.TECH_TECHNICAL_KNOWLEDGE
