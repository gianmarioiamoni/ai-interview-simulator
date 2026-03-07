# app/ui/handlers/written_submit_handler.py

from app.ui.state_handlers import submit_written_answer


def written_submit_handler(controller, state, answer):

    response = submit_written_answer(
        controller,
        state,
        answer,
    )

    return response.to_gradio_outputs()
