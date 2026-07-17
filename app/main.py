# Application entry point

from app.core.logger import configure_logging, get_logger
from app.ui.app import build_app
from services.corpus_persistence.corpus_loader import ensure_corpus

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    from infrastructure.config.settings import settings

    hf_token = settings.hf_token
    ensure_corpus(hf_token=hf_token)

    logger.info("Creating Gradio app...")
    app = build_app()
    host = settings.server_host
    port = settings.server_port
    logger.info("Launching Gradio app on http://%s:%s", host, port)
    app.launch(
        server_name=host,
        server_port=port,
        share=False,
        quiet=False,
    )


if __name__ == "__main__":
    main()
