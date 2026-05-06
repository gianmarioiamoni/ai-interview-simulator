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

        ui_state = UIStateMachine.resolve(state)

        if ui_state.name == "SETUP":
            return self._build_setup(state)

        if ui_state.name == "QUESTION":
            return self._build_question(state)

        if ui_state.name == "FEEDBACK":
            return self._build_feedback(state)

        if ui_state.name == "REPORT":
            return self._build_report(state)

        # fallback safety
        return self._build_setup(state)

    # =====================================================
    # SETUP
    # =====================================================
    def _build_setup(self, state: InterviewState) -> UIResponse:

        return UIResponse(
            state=state,
            role_visible=True,
            interview_type_visible=True,
            company_visible=True,
            language_visible=True,
            start_button_visible=True,
            page_title="## Configure Your Interview",
        )

    # =====================================================
    # QUESTION
    # =====================================================
    def _build_question(self, state: InterviewState) -> UIResponse:

        mapper = InterviewStateMapper()
        session_dto = mapper.to_session_dto(state)

        question = session_dto.current_question
        if question is None:
            return self._build_setup(state)

        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        display = DisplaySection.build(state, question, "QUESTION", attempts > 0)
        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, "QUESTION", can_retry)

        start_button_interactive = (
            state.role is not None
            and state.company
            and state.interview_type is not None
        )

        # loader decision
        loader_visible, loader_value = self._resolve_loader(state)

        return self._build_base_question_ui(
            state=state,
            question=question,
            display=display,
            counter=counter,
            feedback="",
            buttons=buttons,
            start_button_interactive=start_button_interactive,
            loader_visible=loader_visible,
            loader_value=loader_value,
        )

    # =====================================================
    # FEEDBACK
    # =====================================================
    def _build_feedback(self, state: InterviewState) -> UIResponse:

        mapper = InterviewStateMapper()
        session_dto = mapper.to_session_dto(state)

        question = session_dto.current_question
        if question is None:
            return self._build_setup(state)

        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        display = DisplaySection.build(state, question, "FEEDBACK", attempts > 0)
        feedback = FeedbackSection.build(state)
        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, "FEEDBACK", can_retry)

        # loader decision
        loader_visible, loader_value = self._resolve_loader(state)

        return self._build_base_question_ui(
            state=state,
            question=question,
            display=display,
            counter=counter,
            feedback=feedback,
            buttons=buttons,
            start_button_interactive=start_button_interactive,
            loader_visible=loader_visible,
            loader_value=loader_value,
        )

    # =====================================================
    # REPORT
    # =====================================================
    def _build_report(self, state: InterviewState) -> UIResponse:

        return UIResponse(
            state=state,
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title="## Final Report",
            report_output="Report ready",
        )

    # =====================================================
    # SHARED QUESTION BUILDER
    # =====================================================
    def _build_base_question_ui(
        self,
        state: InterviewState,
        question,
        display,
        counter,
        feedback,
        buttons,
        start_button_interactive,
        loader_visible,
        loader_value,
    ) -> UIResponse:

        # DISPLAY CONTENT
        written_display = f"<div>{display.get('written_display', '')}</div>"
        coding_display = display.get("coding_display", "")
        database_display = display.get("database_display", "")

        # TYPE FLAGS
        is_written = question.type == QuestionType.WRITTEN
        is_coding = question.type == QuestionType.CODING
        is_database = question.type == QuestionType.DATABASE

        # TITLE
        if isinstance(question.area, str):
            area_label = question.area
        else:
            area_label = question.area.name.replace("_", " ").title()

        page_title = f"## {area_label}"

        # EDITOR DEFAULTS
        editor_value = ""
        if is_coding:
            editor_value = "# Write your solution here"
        elif is_database:
            editor_value = "-- Write your SQL query here"

        # BUTTON LABEL
        if is_coding:
            submit_label = "Run Code"
        elif is_database:
            submit_label = "Run Query"
        else:
            submit_label = "Submit Answer"

        return UIResponse(
            state=state,
            # HIDE SETUP
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            # HEADER
            page_title=page_title,
            question_counter=counter,
            feedback_markdown=feedback,
            # DISPLAY
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            written_visible=is_written,
            coding_visible=is_coding,
            database_visible=is_database,
            # BUTTONS
            show_submit=buttons["show_submit"],
            submit_interactive=False,
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons.get("next_label") or "",
            submit_label=submit_label,
            # EDITORS
            written_editor_value=editor_value if is_written else "",
            coding_editor_value=editor_value if is_coding else "",
            database_editor_value=editor_value if is_database else "",
            written_editor_visible=is_written,
            coding_editor_visible=is_coding,
            database_editor_visible=is_database,
            # START BUTTON
            start_button_interactive=start_button_interactive,
            # LOADER
            loader_visible=loader_visible,
            loader_value=loader_value,
        )

    # =====================================================
    # SHARED LOADER BUILDER
    # =====================================================
    def _resolve_loader(self, state):
        if not getattr(state, "current_step", None):
            return False, ""

        step_map = {
            "validating": "🔍 Validating...",
            "processing": "🧠 Processing...",
            "evaluating": "📊 Evaluating...",
        }

        return True, step_map.get(state.current_step, "Processing...")
