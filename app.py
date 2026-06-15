# app.py — Hugging Face Spaces entrypoint

import os

from app.core.logger import configure_logging, get_logger
from app.ui.app import build_app

configure_logging()
logger = get_logger(__name__)

logger.info("Building Gradio app for HF Spaces...")

demo = build_app()

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
    )
