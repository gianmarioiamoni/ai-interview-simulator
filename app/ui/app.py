# app/ui/app.py

import gradio as gr

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController

from app.ui.views.setup_view import SetupView
from app.ui.state_handlers import submit_answer
from app.ui.views.interview_view import InterviewView


def build_app():

    graph = build_graph()
    mapper = InterviewStateMapper()
    controller = InterviewController(graph, mapper)

    with gr.Blocks() as demo:

        gr.Markdown("# AI Interview Simulator")

        state = gr.State()

        # -------------------------
        # Setup
        # -------------------------

        setup_view = SetupView(controller)
        setup_view.render(state)

        # -------------------------
        # Interview
        # -------------------------

        interview_view = InterviewView()
        question_counter, question_text, answer_box, submit_button = (
            interview_view.render()
        )

        report_output = gr.Markdown(visible=False)

        submit_button.click(
            lambda s, a: submit_answer(controller, s, a),
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
