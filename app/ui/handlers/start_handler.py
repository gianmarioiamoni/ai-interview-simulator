# app/ui/handlers/start_handler.py

from app.ui.state_handlers import start_interview
from app.ui.utils.loading_utils import show_loader, hide_loader


def start_handler(role, interview_type, company, language):

    # -------------------------------------------------
    # STEP 1 — SHOW LOADER (NO UI CHANGES)
    # -------------------------------------------------

    # idle updates for all outputs
    # (None = do not modify anything)
    base = [None] * (len(response.to_gradio_outputs()) - 1)

    yield tuple(
        [
            *base,
            show_loader(
                "⏳ Generating interview. It can take a few minutes. Please wait..."
            ),
        ]
    )

    # -------------------------------------------------
    # STEP 2 — EXECUTE LOGIC
    # -------------------------------------------------

    response = start_interview(
        role=role,
        interview_type=interview_type,
        company=company,
        language=language,
    )

    # -------------------------------------------------
    # STEP 3 — FINAL UI + HIDE LOADER
    # -------------------------------------------------

    outputs = list(response.to_gradio_outputs())

    # loader è sempre ultimo
    outputs[-1] = hide_loader()

    yield tuple(outputs)
