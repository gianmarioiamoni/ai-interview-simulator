# Application entry point

from app.core.logger import configure_logging, get_logger
from app.process_edge.asgi import build_process_asgi_app, run_process_app
from app.ui.app import build_app
from services.corpus_persistence.corpus_loader import ensure_corpus

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    from infrastructure.config.settings import settings

    hf_token = settings.hf_token
    ensure_corpus(hf_token=hf_token)

    logger.info("Creating Gradio app...")
    demo = build_app()
    asgi_app = build_process_asgi_app(demo, settings=settings)
    host = settings.server_host
    port = settings.server_port
    logger.info("Launching process app on http://%s:%s", host, port)
    run_process_app(asgi_app, host=host, port=port)


if __name__ == "__main__":
    main()
