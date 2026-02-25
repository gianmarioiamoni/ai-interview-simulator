# app/ui/app_real.py

import gradio as gr

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.role import Role, RoleType

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController
from app.ui.sample_data_loader import load_sample_questions


# ---------------------------------------------------------
# Wiring
# ---------------------------------------------------------

graph = build_graph()
mapper = InterviewStateMapper()
controller = InterviewController(graph, mapper)


# ---------------------------------------------------------
# Handlers
# ---------------------------------------------------------


def start_interview():
    questions = load_sample_questions()

    state = InterviewState(
        interview_id="demo-session",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Demo Company",
        language="en",
        questions=questions,
        progress=InterviewProgress.SETUP,
    )

    session_dto = controller.start_interview(state)

    return (
        state,
        session_dto.current_question.text,
        f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
        "",
        gr.update(visible=True),
        gr.update(visible=False),
    )


def submit_answer(state: InterviewState, user_answer: str):

    # Stub graph does not store answers, but we simulate flow
    session_or_report = controller.submit_answer(state)

    if hasattr(session_or_report, "overall_score"):
        # Final report
        report = session_or_report

        report_text = f"""
        Overall Score: {report.overall_score}
        Hiring Probability: {report.hiring_probability}%
        """

        return (
            state,
            "",
            "",
            "",
            gr.update(visible=False),
            gr.update(value=report_text, visible=True),
        )

    else:
        session = session_or_report

        return (
            state,
            session.current_question.text,
            f"Question {session.current_question.index}/{session.current_question.total}",
            "",
            gr.update(visible=True),
            gr.update(visible=False),
        )


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

def build_app():
    with gr.Blocks() as demo:

        gr.Markdown("# AI Interview Simulator (Stub Mode)")

        state = gr.State()

        start_button = gr.Button("Start Interview")

        question_counter = gr.Markdown("")
        question_text = gr.Markdown("")
        answer_box = gr.Textbox(label="Your Answer", lines=5)

        submit_button = gr.Button("Submit Answer", visible=False)

        report_output = gr.Markdown(visible=False)

        start_button.click(
            start_interview,
            outputs=[
                state,
                question_text,
                question_counter,
                answer_box,
                submit_button,
                report_output,
            ],
        )

        submit_button.click(
            submit_answer,
            inputs=[state, answer_box],
            outputs=[
                state,
                question_text,
                question_counter,
                answer_box,
                submit_button,
                report_output,
            ],
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch()
