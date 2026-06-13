# Application entry point

from app.ui.app import build_app
from app.core.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Creating Gradio app...")
    app = build_app()
    logger.info("Launching Gradio app on http://localhost:7860")
    app.launch(
        server_name="127.0.0.1", 
        server_port=7860, 
        share=False,
        quiet=False
    )

if __name__ == "__main__":
    main()
