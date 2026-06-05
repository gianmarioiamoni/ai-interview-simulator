# services/question_intelligence/question_difficulty_mapper.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question, QuestionDifficulty
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata

_DIFFICULTY_TO_CORPUS_INT = {
    QuestionDifficulty.EASY: 2,
    QuestionDifficulty.MEDIUM: 3,
    QuestionDifficulty.HARD: 4,
}


def question_difficulty_to_corpus_int(difficulty: QuestionDifficulty) -> int:

    return _DIFFICULTY_TO_CORPUS_INT.get(difficulty, 3)


def question_to_bank_item_stub(question: Question) -> QuestionBankItem:

    return QuestionBankItem(
        id=question.id,
        text=question.prompt,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=question.area,
        level=SeniorityLevel.MID,
        difficulty=question_difficulty_to_corpus_int(question.difficulty),
        ingestion_metadata=IngestionMetadata(
            source_name="runtime_stub",
            source_type="question_set_progression",
            dataset_version="v1",
            ingestion_timestamp="2020-01-01T00:00:00Z",
        ),
        provenance=question.provenance,
    )
