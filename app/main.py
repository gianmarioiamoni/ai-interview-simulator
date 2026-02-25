# Application entry point

from app.ui.gradio_app import create_app

def main() -> None:
    print("Creating Gradio app...")
    app = create_app()
    print("Launching Gradio app on http://localhost:7860")
    app.launch(
        server_name="127.0.0.1", 
        server_port=7860, 
        share=False,
        quiet=False
    )

if __name__ == "__main__":
    main()
