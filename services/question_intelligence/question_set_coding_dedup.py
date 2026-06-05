# services/question_intelligence/question_set_coding_dedup.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question
from domain.contracts.question.question_origin_type import QuestionOriginType


def is_corpus_backed_coding_question(question: Question) -> bool:

    if question.area != InterviewArea.TECH_CODING:
        return False

    provenance = question.provenance

    return bool(
        provenance
        and provenance.origin_type == QuestionOriginType.RETRIEVAL
        and provenance.generated_by_model == "coding_question_enrichment",
    )


def prioritize_corpus_coding_for_dedup(questions: list[Question]) -> list[Question]:

    """Place corpus-backed coding questions before generated fallback coding (dedup keeps first)."""

    if len(questions) < 2:
        return questions

    non_coding: list[Question] = []
    corpus_coding: list[Question] = []
    fallback_coding: list[Question] = []

    for question in questions:
        if question.area != InterviewArea.TECH_CODING:
            non_coding.append(question)
        elif is_corpus_backed_coding_question(question):
            corpus_coding.append(question)
        else:
            fallback_coding.append(question)

    return non_coding + corpus_coding + fallback_coding
