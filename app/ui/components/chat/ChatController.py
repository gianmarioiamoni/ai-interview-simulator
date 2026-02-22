# Chat controller: UI orchestration only

import gradio as gr
from app.orchestration.rag_pipeline import RAGPipeline

class ChatController:
    def __init__(self) -> None:
        self._pipeline = RAGPipeline()

    def render(self) -> None:
        chatbot = gr.Chatbot()
        input_box = gr.Textbox(label="Your question")

        input_box.submit(
            self._handle_message,
            inputs=input_box,
            outputs=chatbot
        )

    def _handle_message(self, message: str, history: list) -> list:
        answer = self._pipeline.run(message)
        history.append((message, answer))
        return history
