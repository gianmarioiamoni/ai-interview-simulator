# app.py — Hugging Face Spaces entrypoint

import os

from app.core.logger import configure_logging, get_logger
from app.ui.app import build_app
from services.corpus_persistence.corpus_loader import ensure_corpus

configure_logging()
logger = get_logger(__name__)

hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
ensure_corpus(hf_token=hf_token)

logger.info("Building Gradio app for HF Spaces...")

demo = build_app()

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
    )
