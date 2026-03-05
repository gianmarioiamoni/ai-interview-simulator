# app/ui/app.py

import gradio as gr

from app.graph.builder import build_graph

from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController
from app.ui.layout.ui_layout import build_layout
from app.ui.bindings.ui_bindings import bind_events
from app.core.flow.interview_flow_engine import InterviewFlowEngine

def build_app():

    graph = build_graph()
    mapper = InterviewStateMapper()
    controller = InterviewController(graph, mapper)
    flow_engine = InterviewFlowEngine(controller)

    with gr.Blocks(
        css="""
        #code-editor textarea {
            font-family: monospace;
        }
        """
    ) as demo:

        components = build_layout()

        bind_events(
            flow_engine=flow_engine,
            components=components,
        )

    return demo
