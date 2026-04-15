# app/ui/bindings/validators/submit_enabler.py

import gradio as gr


class SubmitEnabler:

    def enable(self, text):

        # normalize input
        if text is None:
            return gr.update(interactive=False)

        if isinstance(text, str):
            text = text.strip()

        # enable only if real content exists
        is_valid = bool(text)

        return gr.update(interactive=is_valid)
