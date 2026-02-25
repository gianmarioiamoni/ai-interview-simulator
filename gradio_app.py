# gradio_app.py

import os
from app.ui.app_real import build_app

if not os.getenv("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY not set")

app = build_app()

app.launch(server_name="0.0.0.0", server_port=7860)
