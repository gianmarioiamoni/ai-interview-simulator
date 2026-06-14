# app/ui/bindings/validators/input_validator.py

import gradio as gr


class InputValidator:
    def validate(
        self,
        role,
        role_custom_name,
        interview_type,
        seniority,
        interview_length,
        company,
        language,
    ):
        role_valid = role is not None
        if role == "other":
            role_valid = bool(role_custom_name and role_custom_name.strip())

        valid = (
            role_valid
            and interview_type is not None
            and seniority is not None
            and interview_length is not None
            and company is not None
            and company.strip() != ""
            and language is not None
        )
        return gr.update(interactive=valid)
