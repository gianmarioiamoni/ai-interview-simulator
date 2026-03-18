# app/ui/layout/interview_layout_builder.py

from app.ui.views.interview_written_view import InterviewWrittenView
from app.ui.views.interview_coding_view import InterviewCodingView
from app.ui.views.interview_database_view import InterviewDatabaseView


def build_interview_views():

    written = InterviewWrittenView().build()
    coding = InterviewCodingView().build()
    database = InterviewDatabaseView().build()

    return {
        "written": written,
        "coding": coding,
        "database": database,
    }
