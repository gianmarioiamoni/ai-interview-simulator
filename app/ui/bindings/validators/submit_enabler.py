# app/ui/bindings/validators/submit_enabler.py

import gradio as gr

from domain.contracts.question.question import QuestionType


class SubmitEnabler:

    def enable(self, state, written, coding, database):
        # Enable submit button based on the current question type and the content of the corresponding input.

        # -----------------------------------------------------
        # SAFETY: invalid state
        # -----------------------------------------------------
        if state is None or not getattr(state, "current_question", None):
            return gr.update(interactive=False)

        q = state.current_question

        # -----------------------------------------------------
        # DETERMINE ACTIVE INPUT
        # -----------------------------------------------------

        if q.is_written():
            value = written
        elif q.is_coding():
            value = coding
        elif q.is_database():
            value = database
        else:
            return gr.update(interactive=False)

        # -----------------------------------------------------
        # NORMALIZATION
        # -----------------------------------------------------
        if value is None:
            return gr.update(interactive=False)

        if isinstance(value, str):
            normalized = value.strip()
        else:
            normalized = str(value).strip()

        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------
        is_valid = len(normalized) > 0

        # -----------------------------------------------------
        # OUTPUT
        # -----------------------------------------------------
        return gr.update(interactive=is_valid)
