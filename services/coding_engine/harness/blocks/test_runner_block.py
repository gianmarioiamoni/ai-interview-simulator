# services/coding_engine/harness/blocks/test_runner_block.py

import os
from typing import List
from .base_block import BaseBlock

from services.coding_engine.harness.markers import TestMarkers
from services.coding_engine.harness.template_renderer import TemplateRenderer

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "../templates")

class TestRunnerBlock(BaseBlock):

    def __init__(self, visible_tests, hidden_tests):
        self.visible_tests = visible_tests
        self.hidden_tests = hidden_tests

        self._renderer = TemplateRenderer(TEMPLATES_DIR)

    def render(self) -> List[str]:

        context = {
            "visible_tests": self._serialize_tests(self.visible_tests),
            "hidden_tests": self._serialize_tests(self.hidden_tests),
            "total_visible": len(self.visible_tests),
            "total_hidden": len(self.hidden_tests),
            "markers": TestMarkers,
        }

        rendered = self._renderer.render("test_runner.j2", context)

        return rendered.split("\n")

    # =========================================================
    # INTERNALS
    # =========================================================

    def _serialize_tests(self, tests):

        serialized = []

        for t in tests:
            serialized.append(
                {
                    "args": repr(t.args),
                    "kwargs": repr(t.kwargs),
                    "expected": repr(t.expected),
                }
            )

        return serialized
