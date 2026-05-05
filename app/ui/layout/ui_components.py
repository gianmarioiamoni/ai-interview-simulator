from dataclasses import dataclass


@dataclass
class UILayoutComponents:

    # STATE
    state: object

    # SETUP INPUTS
    role_input: object
    interview_type_input: object
    company_input: object
    language_input: object
    start_button: object
    page_title: object

    # HEADER
    question_counter: object
    feedback_output: object

    # DISPLAY
    written_display: object
    coding_display: object
    database_display: object

    # EDITORS
    written_box: object
    coding_box: object
    database_box: object

    # BUTTONS
    submit_button: object
    retry_button: object
    next_button: object

    # REPORT
    final_feedback: object
    report_output: object

    # LOADER
    global_loader: object
