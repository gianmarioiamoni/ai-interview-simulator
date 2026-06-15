# Application entry point

import os

from app.ui.app import build_app
from app.core.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    logger.info("Creating Gradio app...")
    app = build_app()
    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 7860))
    logger.info("Launching Gradio app on http://%s:%s", host, port)
    app.launch(
        server_name=host,
        server_port=port,
        share=False,
        quiet=False,
    )


if __name__ == "__main__":
    main()
