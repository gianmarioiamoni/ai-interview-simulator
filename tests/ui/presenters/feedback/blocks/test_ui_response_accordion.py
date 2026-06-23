# tests/ui/presenters/feedback/blocks/test_ui_response_accordion.py

import pytest
from app.ui.ui_response import UIResponse
from app.contracts.output_contract import OUTPUT_KEYS


class TestUIResponseAccordion:

    def test_advanced_context_visible_true_by_default(self):
        r = UIResponse(state=None)
        assert r.advanced_context_visible is True

    def test_advanced_context_can_be_set_false(self):
        r = UIResponse(state=None, advanced_context_visible=False)
        assert r.advanced_context_visible is False

    def test_output_contract_includes_accordion_key(self):
        assert "advanced_context_accordion" in OUTPUT_KEYS

    def test_accordion_key_after_language_dropdown(self):
        idx_lang = OUTPUT_KEYS.index("language_dropdown")
        idx_acc = OUTPUT_KEYS.index("advanced_context_accordion")
        assert idx_acc == idx_lang + 1
