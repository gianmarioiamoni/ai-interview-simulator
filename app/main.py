# Application entry point

from app.ui.gradio_app import create_app

def main() -> None:
    app = create_app()
    app.launch()

if __name__ == "__main__":
    main()
