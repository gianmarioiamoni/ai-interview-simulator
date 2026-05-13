# app/ui/adapters/ui_output_adapter.py

from app.ui.ui_response import UIResponse
from app.ui.mappers.output_mapper import OutputMapper


class UIOutputAdapter:

    @staticmethod
    def to_gradio(response: UIResponse):

        return OutputMapper.map(response.to_dict())
