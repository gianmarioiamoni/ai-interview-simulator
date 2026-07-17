# tests/ui/presentation/test_keyboard_primary_flows.py
# EPIC-07 P6/C11 — EC-AX-01 AX-01 keyboard primary-flow verification.

from __future__ import annotations

import inspect

import gradio as gr
import pytest

from app.ui.layout.layout_builder import UILayoutBuilder
from app.ui.layout.sections.report_section import render_report_section
from app.ui.layout.sections.replay_section import render_replay_section
from app.ui.layout.sections.session_history_section import render_session_history_section
from app.ui.presentation import (
    AX01_REQUIREMENT_ID,
    AX01_SURFACES,
    AX01_VERIFICATION_ARTIFACT_TYPE,
    KEYBOARD_OPERABLE_COMPONENT_NAMES,
    PRIMARY_FLOW_CONTROLS,
    assert_keyboard_operable_primary_control,
    component_accessible_name,
    component_config_name,
    primary_flow_controls_by_surface,
)


def _build_layout_components():
    with gr.Blocks():
        return UILayoutBuilder().build()


class TestAx01Inventory:
    def test_requirement_row_metadata(self) -> None:
        assert AX01_REQUIREMENT_ID == "AX-01"
        assert AX01_VERIFICATION_ARTIFACT_TYPE == "Keyboard path test"
        assert AX01_SURFACES == frozenset(
            {"setup", "question", "feedback", "report", "replay", "history"}
        )

    def test_every_ax01_surface_has_primary_controls(self) -> None:
        by_surface = primary_flow_controls_by_surface()
        assert set(by_surface) == AX01_SURFACES
        for surface_id in AX01_SURFACES:
            assert by_surface[surface_id], f"AX-01 surface missing controls: {surface_id}"

    def test_primary_flow_ids_cover_contract_paths(self) -> None:
        flow_ids = {c.flow_id for c in PRIMARY_FLOW_CONTROLS}
        required_prefixes = (
            "setup.",
            "question.",
            "feedback.",
            "report.",
            "replay.",
            "history.",
        )
        for prefix in required_prefixes:
            assert any(fid.startswith(prefix) for fid in flow_ids), prefix


class TestAx01KeyboardPathOnLiveHost:
    @pytest.fixture(scope="class")
    def components(self):
        return _build_layout_components()

    def test_all_primary_controls_are_keyboard_operable(self, components) -> None:
        for control in PRIMARY_FLOW_CONTROLS:
            component = getattr(components, control.component_attr)
            assert_keyboard_operable_primary_control(component)
            assert component_accessible_name(component) == control.expected_accessible_name
            assert component_config_name(component) in KEYBOARD_OPERABLE_COMPONENT_NAMES

    def test_setup_start_is_native_button(self, components) -> None:
        assert isinstance(components.start_button, gr.Button)
        assert component_config_name(components.start_button) == "button"

    def test_submit_next_retry_are_native_buttons(self, components) -> None:
        assert isinstance(components.submit_button, gr.Button)
        assert isinstance(components.next_button, gr.Button)
        assert isinstance(components.retry_button, gr.Button)

    def test_report_actions_are_native_buttons(self, components) -> None:
        assert isinstance(components.pdf_button, gr.DownloadButton)
        assert isinstance(components.json_button, gr.DownloadButton)
        assert isinstance(components.replay_session_button, gr.Button)
        assert isinstance(components.new_interview_button, gr.Button)

    def test_replay_nav_are_native_buttons(self, components) -> None:
        assert isinstance(components.replay_backward_button, gr.Button)
        assert isinstance(components.replay_forward_button, gr.Button)
        assert isinstance(components.replay_exit_button, gr.Button)

    def test_history_to_replay_controls_are_keyboard_operable(self, components) -> None:
        assert isinstance(components.session_history_dropdown, gr.Dropdown)
        assert isinstance(components.replay_from_history_button, gr.Button)
        assert_keyboard_operable_primary_control(components.session_history_dropdown)
        assert_keyboard_operable_primary_control(components.replay_from_history_button)

    def test_language_mode_control_is_keyboard_operable(self, components) -> None:
        assert isinstance(components.enabled_languages_input, gr.CheckboxGroup)
        assert_keyboard_operable_primary_control(components.enabled_languages_input)


class TestAx01NoKeyboardTrapPatterns:
    """No custom HTML-only click hosts for primary actions (Gradio trap risk)."""

    def test_layout_builder_uses_gradio_buttons_for_primary_actions(self) -> None:
        source = inspect.getsource(UILayoutBuilder.build)
        assert 'gr.Button("Start Interview"' in source
        assert 'gr.Button("Submit"' in source
        assert 'gr.Button("Next"' in source
        assert 'gr.Button("Retry"' in source
        assert "onclick" not in source.lower()

    def test_report_section_primary_actions_are_gradio_controls(self) -> None:
        source = inspect.getsource(render_report_section)
        assert "gr.DownloadButton" in source
        assert 'gr.Button(\n            "Replay Session"' in source or 'gr.Button("Replay Session"' in source
        assert 'gr.Button("Start New Interview")' in source
        assert "onclick" not in source.lower()

    def test_replay_section_nav_are_gradio_buttons(self) -> None:
        source = inspect.getsource(render_replay_section)
        assert 'elem_id="replay-backward"' in source
        assert 'elem_id="replay-forward"' in source
        assert 'elem_id="replay-exit"' in source
        assert "gr.Button" in source
        assert "onclick" not in source.lower()

    def test_history_replay_action_is_gradio_button(self) -> None:
        source = inspect.getsource(render_session_history_section)
        assert 'elem_id="replay-from-history"' in source
        assert "gr.Button" in source
        assert "gr.Dropdown" in source
        assert "onclick" not in source.lower()
