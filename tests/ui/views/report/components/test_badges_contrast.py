# tests/ui/views/report/components/test_badges_contrast.py

import pytest
from app.ui.views.report.components.badges import badge, score_badge
from app.ui.views.report.sections.overall_section import render_overall
from app.ui.views.report.sections.market_section import render_market


_BANNED_CONTRAST_COLOR = "#6b7280"


class TestBadgesContrast:

    def test_na_badge_not_using_low_contrast_gray(self):
        html = score_badge(None)
        assert _BANNED_CONTRAST_COLOR not in html

    def test_score_badge_green(self):
        html = score_badge(85)
        assert "#16a34a" in html

    def test_score_badge_yellow(self):
        html = score_badge(65)
        assert "#ca8a04" in html or "#dc2626" in html  # threshold-dependent

    def test_score_badge_red(self):
        html = score_badge(10)
        assert "#dc2626" in html


class TestOverallSectionContrast:

    def _make_report(self):
        import types
        r = types.SimpleNamespace()
        r.raw_score = 70.0
        r.adjusted_score = 75.0
        r.overall_score = 75.0
        r.hire_decision = "HIRE"
        r.hiring_probability = 80.0
        r.gating_triggered = False
        r.gating_reason = None
        r.seniority_level = "mid"
        r.context_profile = None
        return r

    def test_base_score_label_no_low_contrast_gray(self):
        html = render_overall(self._make_report())
        assert _BANNED_CONTRAST_COLOR not in html


class TestMarketSectionContrast:

    def test_percentile_explanation_no_low_contrast_gray(self):
        import types
        report = types.SimpleNamespace()
        report.overall_score = 72.0
        report.percentile_rank = 60.0
        report.percentile_explanation = "Above average performance."
        report.role = None

        from domain.contracts.user.role import RoleType
        report.role = RoleType.BACKEND_ENGINEER

        vm = {
            "report": report,
            "percentile_segment": "Above Average",
            "percentile_narrative": "Good candidate.",
        }
        html = render_market(vm)
        assert _BANNED_CONTRAST_COLOR not in html
