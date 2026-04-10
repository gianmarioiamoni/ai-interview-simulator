# app/ui/bindings/validators/submit_enabler.py

import gradio as gr


class SubmitEnabler:
    def enable(self, text):
        if text and str(text).strip():
            return gr.update(interactive=True)
        return gr.update(interactive=False)
