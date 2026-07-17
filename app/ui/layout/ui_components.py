# app/ui/layout/ui_components.py

from dataclasses import dataclass


@dataclass
class UILayoutComponents:
    state: object

    role_input: object
    role_custom_name_input: object
    interview_type_input: object
    seniority_input: object
    interview_length_input: object
    company_input: object
    language_input: object
    enabled_languages_input: object
    job_description_input: object
    company_description_input: object
    advanced_context_accordion: object
    start_button: object
    page_title: object

    question_counter: object
    feedback_output: object

    written_display: object
    coding_display: object
    database_display: object

    written_box: object
    coding_box: object
    database_box: object

    submit_button: object
    retry_button: object
    next_button: object

    final_feedback: object
    report_output: object
    report_section: object
    pdf_button: object
    json_button: object
    replay_session_button: object
    new_interview_button: object

    global_loader: object

    # EPIC-04 Phase 5 — Replay layout
    replay_section: object
    replay_page_title: object
    replay_nav_progress: object
    replay_backward_button: object
    replay_forward_button: object
    replay_question_panel: object
    replay_summary_panel: object
    replay_scoring_panel: object
    replay_coaching_panel: object
    replay_error_panel: object
    replay_exit_button: object
    replay_runtime: object

    session_history_section: object
    session_history_dropdown: object
    replay_from_history_button: object
