# app/ui/bindings/validators/input_validator.py

import gradio as gr


class InputValidator:
    def validate(self, role, interview_type, company, language):
        valid = (
            role is not None
            and interview_type is not None
            and company is not None
            and company.strip() != ""
            and language is not None
        )
        return gr.update(interactive=valid)
