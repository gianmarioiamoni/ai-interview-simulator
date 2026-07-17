# tests/ui/presentation/test_report_replay_a11y.py
# EPIC-07 P6/C12 — EC-AX-01 AX-02…AX-05 report/replay a11y verification.

from __future__ import annotations

from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.presentation import (
    ACCESSIBILITY_REQUIREMENT_ROWS,
    AX02_REQUIREMENT_ID,
    AX02_SURFACES,
    AX02_VERIFICATION_ARTIFACT_TYPE,
    AX03_REQUIREMENT_ID,
    AX03_SURFACES,
    AX03_VERIFICATION_ARTIFACT_TYPE,
    AX04_REQUIREMENT_ID,
    AX04_SURFACES,
    AX04_VERIFICATION_ARTIFACT_TYPE,
    AX05_REQUIREMENT_ID,
    AX05_SURFACES,
    AX05_VERIFICATION_ARTIFACT_TYPE,
    AsyncBoundary,
    CANDIDATE_FACING_ERROR_CATALOG,
    EMPTY_COPY_CATALOG,
    EXECUTION_ERROR_CATALOG,
    assert_html_images_have_alt,
    assert_perceivable_text,
    assert_replay_html_a11y_hooks,
    assert_report_html_a11y_hooks,
    assert_score_meaning_not_color_only,
    emit_boundary_error,
    is_perceivable_text,
    present_report_surface,
    present_replay_surface,
    surface_status_message,
)
from app.ui.replay.panels.replay_error_boundary import ReplayErrorBoundary
from app.ui.replay.panels.replay_question_panel import ReplayQuestionPanel
from app.ui.replay.panels.replay_scoring_panel import ReplayScoringPanel
from app.ui.replay.panels.replay_session_summary_panel import ReplaySessionSummaryPanel
from app.ui.replay.replay_html_composer import (
    compose_error_html,
    compose_question_html,
    compose_scoring_html,
    compose_summary_html,
)
from app.ui.views.report.charts.distribution_chart import percentile_distribution
from app.ui.views.report.charts.radar_chart import radar_chart
from app.ui.views.report.components.badges import score_badge
from app.ui.views.report.components.tables import contribution_table
from app.ui.views.report.report_renderer import ReportRenderer
from app.ui.views.report.report_view_model_builder import ReportViewModelBuilder
from tests.domain.contracts.report.conftest import make_report
from tests.ui.replay.conftest import (
    make_question_record,
    make_replay_session,
    make_scoring_snapshot,
)


class TestAx02ToAx05Inventory:
    def test_requirement_rows_cover_ax02_through_ax05(self) -> None:
        ids = {row.requirement_id for row in ACCESSIBILITY_REQUIREMENT_ROWS}
        assert ids == {
            AX02_REQUIREMENT_ID,
            AX03_REQUIREMENT_ID,
            AX04_REQUIREMENT_ID,
            AX05_REQUIREMENT_ID,
        }

    def test_verification_artifact_types(self) -> None:
        assert AX02_VERIFICATION_ARTIFACT_TYPE == "Report a11y audit/test"
        assert AX03_VERIFICATION_ARTIFACT_TYPE == "Replay a11y audit/test"
        assert AX04_VERIFICATION_ARTIFACT_TYPE == "Copy presence test"
        assert AX05_VERIFICATION_ARTIFACT_TYPE == "A11y audit/test"

    def test_surface_scopes(self) -> None:
        assert AX02_SURFACES == frozenset({"report"})
        assert AX03_SURFACES == frozenset({"replay"})
        assert "question" in AX04_SURFACES and "feedback" in AX04_SURFACES
        assert AX05_SURFACES == frozenset({"report", "replay"})


class TestAx02ReportHtmlA11y:
    def test_report_html_passes_a11y_hooks(self) -> None:
        dto = FinalReportDTO.from_report(make_report())
        vm = ReportViewModelBuilder().build(dto)
        html = ReportRenderer().render(vm)
        assert_report_html_a11y_hooks(html)

    def test_distribution_chart_img_has_alt(self) -> None:
        html = percentile_distribution(70)
        assert_html_images_have_alt(html, context="AX-02 distribution chart")
        assert 'alt="Role score distribution chart with candidate score marker"' in html

    def test_radar_chart_img_has_alt(self) -> None:
        html = radar_chart(["depth", "clarity"], [70.0, 80.0])
        assert_html_images_have_alt(html, context="AX-02 radar chart")
        assert 'alt="Scoring dimensions radar chart"' in html


class TestAx03ReplayHtmlA11y:
    def test_replay_panel_html_passes_a11y_hooks(self) -> None:
        session = make_replay_session(scoring_snapshot=make_scoring_snapshot())
        summary = compose_summary_html(ReplaySessionSummaryPanel(session).render())
        question = compose_question_html(
            ReplayQuestionPanel(make_question_record()).render()
        )
        scoring = compose_scoring_html(ReplayScoringPanel(session).render())
        error = compose_error_html(
            ReplayErrorBoundary(
                make_replay_session(is_successful=False, failure_reason="boom")
            ).render()
        )
        assert_replay_html_a11y_hooks((summary, question, scoring, error))

    def test_replay_error_message_is_perceivable_text(self) -> None:
        model = ReplayErrorBoundary(
            make_replay_session(is_successful=False, failure_reason="boom")
        ).render()
        assert_perceivable_text(model.candidate_message, context="AX-03 replay error")
        html = compose_error_html(model)
        assert model.candidate_message in html


class TestAx04PerceivableCopy:
    def test_empty_copy_catalog_texts_are_perceivable(self) -> None:
        for key, entry in EMPTY_COPY_CATALOG.items():
            assert_perceivable_text(entry.message_text, context=f"empty:{key}")

    def test_candidate_facing_error_catalog_texts_are_perceivable(self) -> None:
        for key, entry in CANDIDATE_FACING_ERROR_CATALOG.items():
            assert_perceivable_text(entry.message_text, context=f"error:{key}")

    def test_execution_error_catalog_texts_are_perceivable(self) -> None:
        for kind, entry in EXECUTION_ERROR_CATALOG.items():
            assert_perceivable_text(
                entry.candidate_message,
                context=f"execution:{kind.value}",
            )

    def test_surface_status_messages_not_icon_only(self) -> None:
        report_empty = present_report_surface(dto_ready=False)
        replay_empty = present_replay_surface(has_questions=False)
        report_error = present_report_surface(
            dto_ready=False,
            error=emit_boundary_error(AsyncBoundary.REPORT_EXPORT),
        )
        assert_perceivable_text(
            surface_status_message(report_empty),
            context="report EMPTY",
        )
        assert_perceivable_text(
            surface_status_message(replay_empty),
            context="replay EMPTY",
        )
        assert_perceivable_text(
            surface_status_message(report_error),
            context="report ERROR",
        )

    def test_icon_only_rejected(self) -> None:
        assert is_perceivable_text("⚠") is False
        assert is_perceivable_text("🔴") is False
        assert is_perceivable_text("") is False
        assert is_perceivable_text("Export failed. Please try again.") is True


class TestAx05DecorativeNotSoleMeaning:
    def test_score_badge_includes_textual_score(self) -> None:
        html = score_badge(85)
        assert_score_meaning_not_color_only(html, context="score_badge")
        assert "/100" in html

    def test_na_badge_includes_text_label(self) -> None:
        html = score_badge(None)
        assert "N/A" in html
        assert_score_meaning_not_color_only(html, context="na_badge")

    def test_contribution_table_status_includes_words(self) -> None:
        import types

        dims = [
            types.SimpleNamespace(name="Depth", score=90, weight=0.5, contribution=45),
            types.SimpleNamespace(name="Clarity", score=50, weight=0.5, contribution=25),
        ]
        html = contribution_table(dims)
        assert "Strong" in html
        assert "Weak" in html or "Medium" in html
        assert_score_meaning_not_color_only(html, context="contribution_table")

    def test_replay_scoring_html_has_numeric_and_labels(self) -> None:
        session = make_replay_session(scoring_snapshot=make_scoring_snapshot())
        html = compose_scoring_html(ReplayScoringPanel(session).render())
        assert "Overall:" in html
        assert_score_meaning_not_color_only(html, context="replay scoring")
