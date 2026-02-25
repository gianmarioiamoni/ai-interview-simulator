# gradio_app.py

from app.ui.app_real import build_app

app = build_app()

app.launch(server_name="0.0.0.0", server_port=7860)
