# app/ui/handlers/submit_handler.py

from app.ui.state_handlers import submit_answer


def submit_handler(controller, state, answer):

    response = submit_answer(
        controller,
        state,
        answer,
    )

    return response.to_gradio_outputs()
