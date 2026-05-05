# app/ui/bindings/validators/submit_enabler.py

import gradio as gr


class SubmitEnabler:

    def enable(self, value):
        # Enable submit button only if input contains real content.
        # Works for:
        # - Textbox (string)
        # - Code editors (string)

        # -----------------------------------------------------
        # SAFETY: None → disabled
        # -----------------------------------------------------
        if value is None:
            return gr.update(interactive=False)

        # -----------------------------------------------------
        # NORMALIZATION
        # -----------------------------------------------------
        if isinstance(value, str):
            normalized = value.strip()
        else:
            # fallback (future-proof, e.g. unexpected types)
            normalized = str(value).strip()

        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------
        is_valid = len(normalized) > 0

        # -----------------------------------------------------
        # OUTPUT
        # -----------------------------------------------------
        return gr.update(interactive=is_valid)
