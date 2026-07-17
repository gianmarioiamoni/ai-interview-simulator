# app/ui/layout/layout_builder.py

import gradio as gr
from datetime import datetime

from app.ui.layout.ui_components import UILayoutComponents
from app.ui.layout.assets.styles import LOADER_STYLE, REPLAY_LAYOUT_STYLE
from app.ui.layout.sections.report_section import render_report_section
from app.ui.layout.sections.replay_section import render_replay_section
from app.ui.layout.sections.session_history_section import render_session_history_section

from domain.contracts.user.role import RoleType
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.seniority_level import SeniorityLevel
from app.settings.constants import DEFAULT_INTERVIEW_LENGTH

INTERVIEW_LENGTHS = [10, 20, 30]


class UILayoutBuilder:
    def build(self):
        gr.HTML(LOADER_STYLE)
        gr.HTML(REPLAY_LAYOUT_STYLE)

        state = gr.State()

        # HEADER
        gr.Markdown("# AI Interview Simulator")
        gr.Markdown("Build: 2026-03-16-A | Runtime: HuggingFace Spaces")
        gr.Markdown("Current run date and time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        gr.Markdown("---")

        page_title = gr.Markdown("## Configure Your Interview")

        role_input = gr.Dropdown(
            choices=[(r.name.replace("_", " ").title(), r.value) for r in RoleType],
            label="Role",
            visible=True,
        )

        role_custom_name_input = gr.Textbox(
            label="Custom Role Name",
            placeholder="e.g. Platform Engineer, Site Reliability Engineer...",
            visible=False,
        )

        interview_type_input = gr.Radio(
            choices=[t.name for t in InterviewType],
            label="Interview Type",
            visible=True,
        )

        seniority_input = gr.Radio(
            choices=[(s.name.title(), s.value) for s in SeniorityLevel],
            value=SeniorityLevel.MID.value,
            label="Seniority Level",
            visible=True,
        )

        interview_length_input = gr.Radio(
            choices=INTERVIEW_LENGTHS,
            value=DEFAULT_INTERVIEW_LENGTH,
            label="Interview Length (questions)",
            visible=True,
        )

        company_input = gr.Textbox(label="Company", visible=True)

        language_input = gr.Dropdown(
            choices=["en", "it"],
            value="en",
            label="UI locale",
            visible=True,
        )

        enabled_languages_input = gr.CheckboxGroup(
            choices=[
                ("Python", "python"),
                ("JavaScript", "javascript"),
                ("TypeScript", "typescript"),
            ],
            value=["python"],
            label="Coding languages (session mode)",
            visible=True,
        )

        with gr.Accordion("Advanced Context (optional)", open=False) as advanced_context_accordion:
            job_description_input = gr.Textbox(
                label="Job Description",
                placeholder="Paste the job description here to tailor the interview questions...",
                lines=5,
                visible=True,
            )
            company_description_input = gr.Textbox(
                label="Company Description",
                placeholder="Describe the company culture, stack, or mission to add context...",
                lines=3,
                visible=True,
            )

        start_button = gr.Button("Start Interview", interactive=False, visible=True)

        question_counter = gr.Markdown("", visible=False)
        feedback_output = gr.Markdown("", visible=False)

        written_display = gr.Markdown("", visible=False)

        coding_display = gr.Code("", language="python", interactive=False, visible=False)
        database_display = gr.Code("", language="sql", interactive=False, visible=False)

        written_box = gr.Textbox(label="Your Answer", lines=5, visible=False)
        coding_box = gr.Code(language="python", lines=20, visible=False)
        database_box = gr.Code(language="sql", lines=10, visible=False)

        submit_button = gr.Button("Submit", visible=False)
        with gr.Row():
            retry_button = gr.Button("Retry", visible=False)
            next_button = gr.Button("Next", visible=False)

        final_feedback = gr.Markdown("", visible=False)
        report_components = render_report_section()
        report_output = report_components["report_output"]
        report_section = report_components["report_section"]
        pdf_button = report_components["pdf_button"]
        json_button = report_components["json_button"]
        replay_session_button = report_components["replay_session_button"]
        new_interview_button = report_components["new_interview_button"]

        history_components = render_session_history_section()
        replay_components = render_replay_section()

        global_loader = gr.HTML("", visible=False, elem_id="global-loader")

        return UILayoutComponents(
            state=state,
            role_input=role_input,
            role_custom_name_input=role_custom_name_input,
            interview_type_input=interview_type_input,
            seniority_input=seniority_input,
            interview_length_input=interview_length_input,
            company_input=company_input,
            language_input=language_input,
            enabled_languages_input=enabled_languages_input,
            job_description_input=job_description_input,
            company_description_input=company_description_input,
            advanced_context_accordion=advanced_context_accordion,
            start_button=start_button,
            page_title=page_title,
            question_counter=question_counter,
            feedback_output=feedback_output,
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            written_box=written_box,
            coding_box=coding_box,
            database_box=database_box,
            submit_button=submit_button,
            retry_button=retry_button,
            next_button=next_button,
            final_feedback=final_feedback,
            report_output=report_output,
            report_section=report_section,
            pdf_button=pdf_button,
            json_button=json_button,
            replay_session_button=replay_session_button,
            new_interview_button=new_interview_button,
            global_loader=global_loader,
            replay_section=replay_components["replay_section"],
            replay_page_title=replay_components["replay_page_title"],
            replay_nav_progress=replay_components["replay_nav_progress"],
            replay_backward_button=replay_components["replay_backward_button"],
            replay_forward_button=replay_components["replay_forward_button"],
            replay_question_panel=replay_components["replay_question_panel"],
            replay_summary_panel=replay_components["replay_summary_panel"],
            replay_scoring_panel=replay_components["replay_scoring_panel"],
            replay_coaching_panel=replay_components["replay_coaching_panel"],
            replay_error_panel=replay_components["replay_error_panel"],
            replay_exit_button=replay_components["replay_exit_button"],
            replay_runtime=replay_components["replay_runtime"],
            session_history_section=history_components["session_history_section"],
            session_history_status=history_components["session_history_status"],
            session_history_dropdown=history_components["session_history_dropdown"],
            replay_from_history_button=history_components["replay_from_history_button"],
        )
