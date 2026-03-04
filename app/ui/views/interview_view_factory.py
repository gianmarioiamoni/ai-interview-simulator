# app/ui/views/interview_view_factory.py

from domain.contracts import Question, QuestionType
from app.ui.views.interview_written_view import InterviewWrittenView
from app.ui.views.interview_coding_view import InterviewCodingView
from app.ui.views.interview_database_view import InterviewDatabaseView


class InterviewViewFactory:
    # Factory responsible for selecting the correct interview view

    @staticmethod
    def create(
        question: Question,
        on_submit,
    ):
        # Select view based on QuestionType

        if question.type == QuestionType.WRITTEN:
            return InterviewWrittenView(question, on_submit)

        if question.type == QuestionType.CODING:
            return InterviewCodingView(question, on_submit)

        if question.type == QuestionType.DATABASE:
            return InterviewDatabaseView(question, on_submit)

        raise ValueError(f"Unsupported QuestionType: {question.type}")
