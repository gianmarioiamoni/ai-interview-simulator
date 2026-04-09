# app/ui/layout/ui_components.py

from dataclasses import dataclass


@dataclass
class UILayoutComponents:

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------
    state: object

    # ---------------------------------------------------------
    # SETUP
    # ---------------------------------------------------------
    role_dropdown: object
    interview_type_radio: object
    company_input: object
    language_dropdown: object
    start_button: object
    start_loading_text: object

    # ---------------------------------------------------------
    # INTERVIEW - COMMON
    # ---------------------------------------------------------
    question_counter: object
    feedback_output: object

    # ---------------------------------------------------------
    # WRITTEN
    # ---------------------------------------------------------
    written_container: object
    written_display: object
    written_box: object
    written_submit: object

    # ---------------------------------------------------------
    # CODING
    # ---------------------------------------------------------
    coding_container: object
    coding_display: object
    coding_box: object
    coding_submit: object

    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------
    database_container: object
    database_display: object
    database_box: object
    database_submit: object

    # ---------------------------------------------------------
    # ACTIONS
    # ---------------------------------------------------------
    retry_button: object
    next_button: object

    # ---------------------------------------------------------
    # SECTIONS
    # ---------------------------------------------------------
    setup_section: object
    interview_section: object
    completion_section: object
    report_section: object

    # ---------------------------------------------------------
    # COMPLETION
    # ---------------------------------------------------------
    final_feedback: object
    view_report_button: object

    # ---------------------------------------------------------
    # REPORT
    # ---------------------------------------------------------
    pdf_button: object
    json_button: object
    pdf_file: object
    json_file: object
    new_interview_button: object
    report_output: object
