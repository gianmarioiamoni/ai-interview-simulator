# app/ui/handlers/coding_submit_handler.py

from app.ui.state_handlers import submit_coding_answer


def coding_submit_handler(controller, state, answer):

    response = submit_coding_answer(
        controller,
        state,
        answer,
    )

    return response.to_gradio_outputs()
