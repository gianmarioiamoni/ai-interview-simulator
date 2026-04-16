# app/ui/layout/sections/header_section.py

import gradio as gr
from app.core.build_info import BuildInfo

from app.ui.layout.assets.CSS import CODE_BLOCK_STYLE
from app.ui.layout.assets.scripts import (
    FOCUS_EDITOR_SCRIPT,
    SCROLL_TOP_SCRIPT,
)


def render_header():

    gr.Markdown("# AI Interview Simulator")
    gr.Markdown(BuildInfo.get_info())

    gr.HTML(CODE_BLOCK_STYLE)
    gr.HTML(FOCUS_EDITOR_SCRIPT)
    gr.HTML(SCROLL_TOP_SCRIPT)
