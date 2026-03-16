# gradio_app.py

import os
from app.ui.app import build_app

if not os.getenv("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY not set")

print("BUILD VERSION: 2026-03-16-A")
app = build_app()

app.launch(server_name="0.0.0.0", server_port=7860)
