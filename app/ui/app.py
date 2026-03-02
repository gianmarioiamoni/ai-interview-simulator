# app/ui/app.py

import gradio as gr

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController

from app.ui.state_handlers import start_interview, submit_answer
from app.ui.views.interview_view import InterviewView
from app.ui.views.report_view import build_report_markdown


def build_app():

    graph = build_graph()
    mapper = InterviewStateMapper()
    controller = InterviewController(graph, mapper)

    with gr.Blocks() as demo:

        gr.Markdown("# AI Interview Simulator")

        state = gr.State()

        interview_view = InterviewView()

        question_counter, question_text, answer_box, submit_button = (
            interview_view.render()
        )

        report_output = gr.Markdown(visible=False)

        start_button = gr.Button("Start Interview")

        start_button.click(
            lambda: start_interview(controller),
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
