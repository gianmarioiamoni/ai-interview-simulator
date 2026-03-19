# app/ui/types/ui_fields.py

from typing import TypedDict


class DisplayFields(TypedDict):
    written_display: str
    coding_display: str
    database_display: str


class VisibilityFields(TypedDict):
    written_visible: bool
    coding_visible: bool
    database_visible: bool


class EditorVisibilityFields(TypedDict):
    written_editor_visible: bool
    coding_editor_visible: bool
    database_editor_visible: bool


class ButtonState(TypedDict):
    show_submit: bool
    show_submit_interactive: bool
    show_retry: bool
    show_next: bool
    next_label: str
