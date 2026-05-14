# gradio_app.py

import os

from app.ui.app import build_app
from app.core.logger import configure_logging, get_logger

configure_logging()

logger = get_logger(__name__)

if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY not set")

logger.info("BUILD VERSION: 2026-03-16-A")

app = build_app()

app.launch(server_name="0.0.0.0", server_port=7860, share=True, show_api=False)
