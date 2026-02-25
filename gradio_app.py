# gradio_app.py

from app.ui.app_real import build_app

demo = build_app()

if __name__ == "__main__":
    demo.launch()
