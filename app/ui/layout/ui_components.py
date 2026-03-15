# app/ui/layout/ui_components.py

from dataclasses import dataclass


@dataclass
class UILayoutComponents:

    state: object

    role_dropdown: object
    interview_type_radio: object
    company_input: object
    language_dropdown: object
    start_button: object

    question_counter: object
    feedback_output: object

    written_container: object
    written_text: object
    written_box: object
    written_submit: object

    coding_container: object
    coding_text: object
    coding_box: object
    coding_submit: object

    database_container: object
    database_text: object
    database_box: object
    database_submit: object

    retry_button: object
    next_button: object

    setup_section: object
    interview_section: object
    completion_section: object
    report_section: object

    final_feedback: object

    view_report_button: object

    pdf_button: object
    json_button: object
    pdf_file: object
    json_file: object

    new_interview_button: object

    report_output: object