# tests/ui/mappers/test_loader_mapper_navigation.py

import pytest
from app.ui.constants.loader_steps import LoaderStep
from app.ui.mappers.loader_mapper import map_loader_text, map_loader_progress


class TestLoaderMapperNavigation:

    def test_loading_next_question_text_not_submitting(self):
        text = map_loader_text(LoaderStep.LOADING_NEXT_QUESTION)
        assert "Submitting" not in text
        assert text != ""

    def test_loading_next_question_has_progress(self):
        progress = map_loader_progress(LoaderStep.LOADING_NEXT_QUESTION)
        assert progress > 0

    def test_submitting_text_unchanged(self):
        text = map_loader_text(LoaderStep.SUBMITTING)
        assert "Submitting" in text

    def test_next_question_text_differs_from_submitting(self):
        submit_text = map_loader_text(LoaderStep.SUBMITTING)
        next_text = map_loader_text(LoaderStep.LOADING_NEXT_QUESTION)
        assert submit_text != next_text
