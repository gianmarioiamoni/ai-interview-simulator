# app/ui/presentation/accessibility_keyboard.py
# EPIC-07 EC-AX-01 AX-01 / Data Model §4.6 — keyboard primary-flow inventory.

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping


AX01_REQUIREMENT_ID: Final[str] = "AX-01"
AX01_VERIFICATION_ARTIFACT_TYPE: Final[str] = "Keyboard path test"

AX01_SURFACES: Final[frozenset[str]] = frozenset(
    {"setup", "question", "feedback", "report", "replay", "history"}
)

# Gradio native widgets that map to keyboard-operable HTML controls (AR-14).
KEYBOARD_OPERABLE_COMPONENT_NAMES: Final[frozenset[str]] = frozenset(
    {
        "button",
        "downloadbutton",
        "dropdown",
        "radio",
        "textbox",
        "checkboxgroup",
        "code",
    }
)


@dataclass(frozen=True)
class PrimaryFlowControl:
    """One primary-flow control subject to AX-01 keyboard operability."""

    flow_id: str
    surface_id: str
    component_attr: str
    expected_accessible_name: str


# EC-AX-01 AX-01 applies_to: setup start, submit/next, report actions,
# replay nav, history→replay (plus setup language-mode control from C5).
PRIMARY_FLOW_CONTROLS: Final[tuple[PrimaryFlowControl, ...]] = (
    PrimaryFlowControl(
        flow_id="setup.language_mode",
        surface_id="setup",
        component_attr="enabled_languages_input",
        expected_accessible_name="Coding languages (session mode)",
    ),
    PrimaryFlowControl(
        flow_id="setup.start",
        surface_id="setup",
        component_attr="start_button",
        expected_accessible_name="Start Interview",
    ),
    PrimaryFlowControl(
        flow_id="question.submit",
        surface_id="question",
        component_attr="submit_button",
        expected_accessible_name="Submit",
    ),
    PrimaryFlowControl(
        flow_id="feedback.retry",
        surface_id="feedback",
        component_attr="retry_button",
        expected_accessible_name="Retry",
    ),
    PrimaryFlowControl(
        flow_id="feedback.next",
        surface_id="feedback",
        component_attr="next_button",
        expected_accessible_name="Next",
    ),
    PrimaryFlowControl(
        flow_id="report.download_pdf",
        surface_id="report",
        component_attr="pdf_button",
        expected_accessible_name="Download PDF",
    ),
    PrimaryFlowControl(
        flow_id="report.download_json",
        surface_id="report",
        component_attr="json_button",
        expected_accessible_name="Download JSON",
    ),
    PrimaryFlowControl(
        flow_id="report.replay_session",
        surface_id="report",
        component_attr="replay_session_button",
        expected_accessible_name="Replay Session",
    ),
    PrimaryFlowControl(
        flow_id="report.new_interview",
        surface_id="report",
        component_attr="new_interview_button",
        expected_accessible_name="Start New Interview",
    ),
    PrimaryFlowControl(
        flow_id="replay.backward",
        surface_id="replay",
        component_attr="replay_backward_button",
        expected_accessible_name="Previous",
    ),
    PrimaryFlowControl(
        flow_id="replay.forward",
        surface_id="replay",
        component_attr="replay_forward_button",
        expected_accessible_name="Next",
    ),
    PrimaryFlowControl(
        flow_id="replay.exit",
        surface_id="replay",
        component_attr="replay_exit_button",
        expected_accessible_name="Exit Replay",
    ),
    PrimaryFlowControl(
        flow_id="history.select",
        surface_id="history",
        component_attr="session_history_dropdown",
        expected_accessible_name="Completed Sessions",
    ),
    PrimaryFlowControl(
        flow_id="history.replay",
        surface_id="history",
        component_attr="replay_from_history_button",
        expected_accessible_name="Replay",
    ),
)


def primary_flow_controls_by_surface() -> Mapping[str, tuple[PrimaryFlowControl, ...]]:
    grouped: dict[str, list[PrimaryFlowControl]] = {s: [] for s in AX01_SURFACES}
    for control in PRIMARY_FLOW_CONTROLS:
        grouped[control.surface_id].append(control)
    return {surface: tuple(items) for surface, items in grouped.items()}


def component_config_name(component: object) -> str:
    get_config = getattr(component, "get_config", None)
    if get_config is None:
        raise TypeError(f"Component lacks get_config: {type(component)!r}")
    name = get_config().get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"Component config missing name: {type(component)!r}")
    return name


def component_accessible_name(component: object) -> str:
    """Visible label/value used as the accessible name for Gradio controls."""
    get_config = getattr(component, "get_config", None)
    if get_config is None:
        raise TypeError(f"Component lacks get_config: {type(component)!r}")
    cfg = get_config()
    label = cfg.get("label")
    if isinstance(label, str) and label.strip():
        return label.strip()
    value = cfg.get("value")
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"Component has no accessible name: {cfg.get('name')!r}")


def assert_keyboard_operable_primary_control(component: object) -> None:
    """AX-01: primary control is a Gradio keyboard-operable widget with text name."""
    name = component_config_name(component)
    if name not in KEYBOARD_OPERABLE_COMPONENT_NAMES:
        raise AssertionError(
            f"AX-01: component type {name!r} is not keyboard-operable "
            f"(allowed={sorted(KEYBOARD_OPERABLE_COMPONENT_NAMES)})"
        )
    accessible = component_accessible_name(component)
    if not accessible:
        raise AssertionError("AX-01: primary control accessible name is empty")
