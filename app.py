# app.py — Hugging Face Spaces entrypoint

from app.core.logger import configure_logging, get_logger
from app.process_edge.asgi import build_process_asgi_app, run_process_app
from app.ui.app import build_app
from infrastructure.config.settings import settings
from services.corpus_persistence.corpus_loader import ensure_corpus

configure_logging()
logger = get_logger(__name__)

ensure_corpus(hf_token=settings.hf_token)

logger.info("Building Gradio app for HF Spaces...")

demo = build_app()
app = build_process_asgi_app(demo, settings=settings)

if __name__ == "__main__":
    run_process_app(app)
