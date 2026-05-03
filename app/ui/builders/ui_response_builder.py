# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.views.report_view import build_report_markdown
from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
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

        if ui_state == UIState.SETUP:
            return self._build_setup(state)

        if ui_state == UIState.REPORT:
            return self._build_report(state)

        if ui_state == UIState.COMPLETION:
            return self._build_completion(state)

        if ui_state in [UIState.QUESTION, UIState.FEEDBACK]:
            return self._build_question(state, session_dto, ui_state)

        raise RuntimeError(f"Unsupported UI state: {ui_state}")

    # ---------------------------------------------------------
    # SETUP
    # ---------------------------------------------------------

    def _build_setup(self, state: InterviewState) -> UIResponse:
        return UIResponse(
            state=state,
            setup_visible=True,
            interview_visible=False,
            completion_visible=False,
            report_visible=False,
            show_submit=False,
            show_retry=False,
            show_next=False,
            question_counter="",
            feedback_markdown="",
        )

    # ---------------------------------------------------------
    # REPORT
    # ---------------------------------------------------------

    def _build_report(self, state: InterviewState) -> UIResponse:

        mapper = InterviewStateMapper()
        report = mapper.to_final_report_dto(state)
        report_md = build_report_markdown(report)

        return UIResponse(
            state=state,
            setup_visible=False,
            interview_visible=False,
            completion_visible=False,
            report_visible=True,
            report_output=report_md,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # ---------------------------------------------------------
    # COMPLETION
    # ---------------------------------------------------------

    def _build_completion(self, state: InterviewState) -> UIResponse:
        return UIResponse(
            state=state,
            setup_visible=False,
            interview_visible=False,
            completion_visible=True,
            report_visible=False,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # ---------------------------------------------------------
    # QUESTION / FEEDBACK
    # ---------------------------------------------------------

    def _build_question(
        self,
        state: InterviewState,
        session_dto: InterviewSessionDTO,
        ui_state: UIState,
    ) -> UIResponse:

        question = session_dto.current_question

        if question is None:
            raise RuntimeError("No question available")

        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        print("\n=== BUILD QUESTION ===")
        print("question type:", question.type)
        print("attempts:", attempts)
        print("can_retry:", can_retry)
        print("========================\n")

        last_answer = state.get_latest_answer_for_question(question.question_id)

        # -------------------------
        # EDITOR VALUE
        # -------------------------

        editor_value = ""

        if last_answer:
            editor_value = last_answer.content
        elif question.type == QuestionType.CODING:
            editor_value = "# Write your solution here"
        elif question.type == QuestionType.DATABASE:
            editor_value = "-- Write your SQL query here"

        # -------------------------
        # DISPLAY
        # -------------------------

        display = DisplaySection.build(
            state,
            question,
            ui_state,
            attempts > 0,
        )

        written_display = display.get("written_display", "")
        coding_display = display.get("coding_display", "")
        database_display = display.get("database_display", "")

        # -------------------------
        # FEEDBACK
        # -------------------------

        feedback_markdown = FeedbackSection.build(state)

        # -------------------------
        # COUNTER
        # -------------------------

        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)

        # -------------------------
        # BUTTONS
        # -------------------------

        buttons = ButtonMapper.map(state, ui_state, can_retry)

        return UIResponse(
            state=state,
            # 🔥 CRUCIALE: SWITCH VIEW
            setup_visible=False,
            interview_visible=True,
            completion_visible=False,
            report_visible=False,
            # HEADER
            question_counter=counter,
            # FEEDBACK
            feedback_markdown=feedback_markdown,
            # DISPLAY
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            # BUTTONS
            show_submit=buttons["show_submit"],
            show_submit_interactive=buttons["show_submit_interactive"],
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons["next_label"],
            # EDITORS
            written_editor_value=(
                editor_value if question.type == QuestionType.WRITTEN else ""
            ),
            coding_editor_value=(
                editor_value if question.type == QuestionType.CODING else ""
            ),
            database_editor_value=(
                editor_value if question.type == QuestionType.DATABASE else ""
            ),
        )
