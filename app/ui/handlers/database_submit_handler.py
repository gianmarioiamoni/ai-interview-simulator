# app/ui/handlers/database_submit_handler.py

from app.ui.state_handlers import submit_database_answer


def database_submit_handler(state, answer):

    response = submit_database_answer(
        state,
        answer,
    )

    return response.to_gradio_outputs()
