# app/ui/presentation/__init__.py
# EPIC-07 P1 — presentation-plane primitives (UI-layer; non-persistent).

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.candidate_facing_error_catalog import (
    CANDIDATE_FACING_ERROR_CATALOG,
    CandidateFacingErrorCatalogEntry,
    get_candidate_facing_error_entry,
)
from app.ui.presentation.empty_copy_catalog import (
    EMPTY_COPY_CATALOG,
    EmptyCopyCatalogEntry,
    get_empty_copy_entry,
)
from app.ui.presentation.surface_ids import DETERMINISTIC_SURFACE_IDS, SURFACE_IDS
from app.ui.presentation.surface_phase import SurfacePhase
from app.ui.presentation.surface_state import SurfaceState
from app.ui.presentation.surface_state_validation import (
    validate_deterministic_surface_not_loading,
    validate_empty_phase_coupling,
    validate_error_phase_coupling,
    validate_loader_allowed,
    validate_surface_id,
)
from app.ui.presentation.boundary_error_emission import (
    BOUNDARY_MESSAGE_KEYS,
    build_error_surface_state,
    emit_boundary_error,
    present_boundary_failure,
)
from app.ui.presentation.session_history_load import (
    SessionHistoryLoadResult,
    load_session_history_list,
    present_session_history_list,
)
from app.ui.presentation.session_history_list_presentation import (
    SessionHistoryItem,
    SessionHistoryListPresentation,
)
from app.ui.presentation.session_config_presentation import SessionConfigPresentation
from app.ui.presentation.session_config_validation import (
    derive_language_mode,
    is_language_mode_complete,
    validate_enabled_languages_vocabulary,
    validate_language_mode_coupling,
    validate_language_mode_not_locale_alone,
)
from app.ui.presentation.execution_error_kind import ExecutionErrorKind
from app.ui.presentation.execution_error_catalog import (
    EXECUTION_ERROR_CATALOG,
    ExecutionErrorCatalogEntry,
    get_execution_error_entry,
)
from app.ui.presentation.execution_error_presentation import (
    ExecutionErrorPresentation,
    classify_execution_error_kind,
    project_execution_error,
)
from app.ui.presentation.question_feedback_surface import (
    FEEDBACK_EMPTY_KEY,
    QUESTION_EMPTY_KEY,
    assert_no_placeholder_chrome,
    assert_texts_have_no_placeholder_chrome,
    empty_copy_text,
    format_execution_error_markdown,
    present_feedback_surface,
    present_question_surface,
    surface_status_message,
)
from app.ui.presentation.report_surface import (
    REPORT_EMPTY_KEY,
    present_report_surface,
    report_loader_visible,
)
from app.ui.presentation.progress_surface import (
    PROGRESS_EMPTY_KEY,
    present_progress_surface,
)
from app.ui.presentation.replay_surface import (
    REPLAY_EMPTY_KEY,
    present_replay_surface,
)

__all__ = [
    "AsyncBoundary",
    "CandidateFacingError",
    "CANDIDATE_FACING_ERROR_CATALOG",
    "CandidateFacingErrorCatalogEntry",
    "get_candidate_facing_error_entry",
    "EMPTY_COPY_CATALOG",
    "EmptyCopyCatalogEntry",
    "get_empty_copy_entry",
    "SURFACE_IDS",
    "DETERMINISTIC_SURFACE_IDS",
    "SurfacePhase",
    "SurfaceState",
    "validate_surface_id",
    "validate_error_phase_coupling",
    "validate_empty_phase_coupling",
    "validate_loader_allowed",
    "validate_deterministic_surface_not_loading",
    "BOUNDARY_MESSAGE_KEYS",
    "build_error_surface_state",
    "emit_boundary_error",
    "present_boundary_failure",
    "SessionHistoryLoadResult",
    "load_session_history_list",
    "present_session_history_list",
    "SessionHistoryItem",
    "SessionHistoryListPresentation",
    "SessionConfigPresentation",
    "derive_language_mode",
    "is_language_mode_complete",
    "validate_enabled_languages_vocabulary",
    "validate_language_mode_coupling",
    "validate_language_mode_not_locale_alone",
    "ExecutionErrorKind",
    "EXECUTION_ERROR_CATALOG",
    "ExecutionErrorCatalogEntry",
    "get_execution_error_entry",
    "ExecutionErrorPresentation",
    "classify_execution_error_kind",
    "project_execution_error",
    "QUESTION_EMPTY_KEY",
    "FEEDBACK_EMPTY_KEY",
    "REPORT_EMPTY_KEY",
    "PROGRESS_EMPTY_KEY",
    "REPLAY_EMPTY_KEY",
    "assert_no_placeholder_chrome",
    "assert_texts_have_no_placeholder_chrome",
    "empty_copy_text",
    "format_execution_error_markdown",
    "present_feedback_surface",
    "present_question_surface",
    "present_report_surface",
    "present_progress_surface",
    "present_replay_surface",
    "report_loader_visible",
    "surface_status_message",
]
