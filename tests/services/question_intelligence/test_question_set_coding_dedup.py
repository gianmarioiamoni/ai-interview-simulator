# tests/services/question_intelligence/test_question_set_coding_dedup.py

from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question, QuestionType
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from services.question_intelligence.question_set_coding_dedup import (
    is_corpus_backed_coding_question,
    prioritize_corpus_coding_for_dedup,
)


def _corpus_coding_question(prompt: str = "Implement two_sum(nums, target).") -> Question:

    return Question(
        id="corpus-coding",
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt=prompt,
        function_name="two_sum",
        coding_spec=CodingSpec(
            type="function",
            entrypoint="two_sum",
            parameters=["nums", "target"],
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
            generated_by_model="coding_question_enrichment",
        ),
    )


def _fallback_coding_question(prompt: str = "Implement two_sum(nums, target).") -> Question:

    return Question(
        id="fallback-coding",
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt=prompt,
        function_name="two_sum",
        coding_spec=CodingSpec(
            type="function",
            entrypoint="two_sum",
            parameters=["nums", "target"],
        ),
        provenance=None,
    )


def test_is_corpus_backed_coding_question() -> None:

    assert is_corpus_backed_coding_question(_corpus_coding_question()) is True
    assert is_corpus_backed_coding_question(_fallback_coding_question()) is False


def test_prioritize_corpus_coding_for_dedup_orders_corpus_before_fallback() -> None:

    fallback = _fallback_coding_question()
    corpus = _corpus_coding_question()
    ordered = prioritize_corpus_coding_for_dedup([fallback, corpus])

    assert ordered.index(corpus) < ordered.index(fallback)


def test_dedup_retains_corpus_backed_coding_over_fallback() -> None:

    fallback = _fallback_coding_question()
    corpus = _corpus_coding_question()

    without_priority = [fallback, corpus]
    with_priority = prioritize_corpus_coding_for_dedup(without_priority)

    def keep_first_only(questions: list[Question]) -> list[Question]:
        return [questions[0]] if questions else []

    kept_without = keep_first_only(without_priority)
    kept_with = keep_first_only(with_priority)

    assert not is_corpus_backed_coding_question(kept_without[0])
    assert is_corpus_backed_coding_question(kept_with[0])
