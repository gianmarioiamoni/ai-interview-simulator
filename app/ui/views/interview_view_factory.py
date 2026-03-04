# app/ui/views/interview_view_factory.py

from app.ui.dto.question_dto import QuestionDTO

from app.ui.views.interview_written_view import InterviewWrittenView
from app.ui.views.interview_coding_view import InterviewCodingView
from app.ui.views.interview_database_view import InterviewDatabaseView


class InterviewViewFactory:
    # Factory responsible for selecting the correct interview view

    @staticmethod
    def create(
        question: QuestionDTO,
        on_submit,
    ):

        question_type = question.question_type

        if question_type == "written":
            return InterviewWrittenView(question, on_submit)

        if question_type == "coding":
            return InterviewCodingView(question, on_submit)

        if question_type == "database":
            return InterviewDatabaseView(question, on_submit)

        raise ValueError(f"Unsupported QuestionType: {question_type}")
