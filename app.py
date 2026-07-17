# app.py — Hugging Face Spaces entrypoint

from app.core.logger import configure_logging, get_logger
from app.ui.app import build_app
from infrastructure.config.settings import settings
from services.corpus_persistence.corpus_loader import ensure_corpus

configure_logging()
logger = get_logger(__name__)

ensure_corpus(hf_token=settings.hf_token)

logger.info("Building Gradio app for HF Spaces...")

demo = build_app()

if __name__ == "__main__":
    demo.launch(
        server_name=settings.server_host,
        server_port=settings.server_port,
        share=False,
    )
