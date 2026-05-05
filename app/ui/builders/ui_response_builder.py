# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from app.ui.ui_response import UIResponse
from app.ui.state_machine.ui_state_machine import UIStateMachine
from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from app.ui.response.sections.display_section import DisplaySection
from app.ui.response.sections.feedback_section import FeedbackSection
from app.ui.response.sections.counter_section import CounterSection
from app.ui.response.config.button_mapper import ButtonMapper

MAX_ATTEMPTS = 3


class UIResponseBuilder:

    def build(self, state: InterviewState) -> UIResponse:

        mapper = InterviewStateMapper()
        session_dto = mapper.to_session_dto(state)

        ui_state = UIStateMachine.resolve(state)

        print("\n=== UI RESPONSE BUILDER DEBUG ===")
        print("ui_state:", ui_state)

        if ui_state.name == "SETUP":
            return UIResponse(
                state=state,
                show_setup=True,
                show_interview=False,
                page_title="## Configure Your Interview",
            )

        if ui_state.name == "REPORT":
            return UIResponse(
                state=state,
                show_setup=False,
                show_interview=True,
                page_title="## Final Report",
                report_output="Report ready",
            )

        question = session_dto.current_question

        print("question:", question)

        if question is None:
            return UIResponse(
                state=state,
                show_setup=False,
                show_interview=True,
            )

        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        display = DisplaySection.build(state, question, ui_state, attempts > 0)
        feedback = FeedbackSection.build(state)
        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        written_display = display.get("written_display", "")
        coding_display = display.get("coding_display", "")
        database_display = display.get("database_display", "")

        print("written_display:", written_display)
        print("coding_display:", coding_display)
        print("database_display:", database_display)

        is_written = question.type == QuestionType.WRITTEN
        is_coding = question.type == QuestionType.CODING
        is_database = question.type == QuestionType.DATABASE

        print("visibility flags:", is_written, is_coding, is_database)

        if isinstance(question.area, str):
            area_label = question.area
        else:
            area_label = question.area.name.replace("_", " ").title()

        page_title = f"## {area_label}"

        editor_value = ""

        if question.type == QuestionType.CODING:
            editor_value = "# Write your solution here"
        elif question.type == QuestionType.DATABASE:
            editor_value = "-- Write your SQL query here"

        submit_label = "Submit"

        if question.type == QuestionType.CODING:
            submit_label = "Run Code"
        elif question.type == QuestionType.DATABASE:
            submit_label = "Run Query"
        elif question.type == QuestionType.WRITTEN:
            submit_label = "Submit Answer"

        return UIResponse(
            state=state,
            show_setup=False,
            show_interview=True,
            page_title=page_title,
            question_counter=counter,
            feedback_markdown=feedback,
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            written_visible=bool(written_display),
            coding_visible=bool(coding_display),
            database_visible=bool(database_display),
            show_submit=buttons["show_submit"],
            show_submit_interactive=buttons["show_submit_interactive"],
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons.get("next_label") or "",
            submit_label=submit_label,
            written_editor_value=editor_value if is_written else "",
            coding_editor_value=editor_value if is_coding else "",
            database_editor_value=editor_value if is_database else "",
            written_editor_visible=is_written,
            coding_editor_visible=is_coding,
            database_editor_visible=is_database,
        )
