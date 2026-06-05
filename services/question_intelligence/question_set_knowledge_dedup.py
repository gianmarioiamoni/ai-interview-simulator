# services/question_intelligence/question_set_knowledge_dedup.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question
from domain.contracts.question.question_origin_type import QuestionOriginType


def is_corpus_backed_knowledge_question(question: Question) -> bool:

    if question.area != InterviewArea.TECH_TECHNICAL_KNOWLEDGE:
        return False

    provenance = question.provenance

    return bool(
        provenance and provenance.origin_type == QuestionOriginType.RETRIEVAL
    )


def prioritize_technical_knowledge_for_dedup(
    questions: list[Question],
) -> list[Question]:

    """Place knowledge questions first so semantic dedup does not drop area coverage."""

    if len(questions) < 2:
        return questions

    corpus_knowledge: list[Question] = []
    fallback_knowledge: list[Question] = []
    other: list[Question] = []

    for question in questions:
        if question.area != InterviewArea.TECH_TECHNICAL_KNOWLEDGE:
            other.append(question)
        elif is_corpus_backed_knowledge_question(question):
            corpus_knowledge.append(question)
        else:
            fallback_knowledge.append(question)

    return corpus_knowledge + fallback_knowledge + other
