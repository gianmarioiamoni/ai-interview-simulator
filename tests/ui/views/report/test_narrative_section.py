# tests/ui/views/report/test_narrative_section.py
# EPIC-V13-05 Phase 10 — render_narrative section tests.
# EPIC-06 C6 — inline evidence from NarrativeInsightDTO (OF-01).

import pytest

from app.ui.dto.final_report_dto import FeatureIdentityDTO, NarrativeInsightDTO
from app.ui.views.report.sections.narrative_section import render_narrative


def _make_insight(
    prose: str = "Candidate shows strong reasoning.",
    insight_type: str = "strength_signal",
    confidence: float = 0.85,
    feature_type_id: str = "reasoning_feature",
    semantic_category: str = "analytical_reasoning",
    is_traceable: bool = True,
) -> NarrativeInsightDTO:
    return NarrativeInsightDTO(
        insight_type=insight_type,
        prose=prose,
        confidence=confidence,
        source_feature_id=FeatureIdentityDTO(
            feature_type_id=feature_type_id,
            semantic_category=semantic_category,
            schema_version="1.0",
        ),
        is_traceable=is_traceable,
    )


class TestRenderNarrative:

    def test_empty_insights_returns_empty_string(self):
        assert render_narrative({"narrative_insights": []}) == ""

    def test_missing_key_returns_empty_string(self):
        assert render_narrative({}) == ""

    def test_renders_prose(self):
        insight = _make_insight(prose="Excellent problem decomposition observed.")
        html = render_narrative({"narrative_insights": [insight]})
        assert "Excellent problem decomposition observed." in html

    def test_renders_insight_type_label(self):
        insight = _make_insight(insight_type="strength_signal")
        html = render_narrative({"narrative_insights": [insight]})
        assert "Strength" in html

    def test_renders_risk_signal_label(self):
        insight = _make_insight(insight_type="risk_signal")
        html = render_narrative({"narrative_insights": [insight]})
        assert "Risk" in html

    def test_renders_confidence(self):
        insight = _make_insight(confidence=0.72)
        html = render_narrative({"narrative_insights": [insight]})
        assert "72%" in html

    def test_renders_multiple_insights(self):
        insights = [
            _make_insight(prose="Insight A"),
            _make_insight(prose="Insight B", insight_type="growth_opportunity"),
        ]
        html = render_narrative({"narrative_insights": insights})
        assert "Insight A" in html
        assert "Insight B" in html

    def test_section_header_present(self):
        insight = _make_insight()
        html = render_narrative({"narrative_insights": [insight]})
        assert "Narrative Insights" in html

    def test_renders_inline_feature_identity_labels(self):
        insight = _make_insight(
            feature_type_id="reasoning_feature",
            semantic_category="analytical_reasoning",
        )
        html = render_narrative({"narrative_insights": [insight]})
        assert "Evidence:" in html
        assert "Reasoning Feature" in html
        assert "Analytical Reasoning" in html

    def test_renders_is_traceable(self):
        insight = _make_insight(is_traceable=True)
        html = render_narrative({"narrative_insights": [insight]})
        assert "Traceable" in html

    def test_renders_not_traceable_when_false(self):
        insight = _make_insight(is_traceable=False)
        html = render_narrative({"narrative_insights": [insight]})
        assert "Not traceable" in html

    def test_evidence_rendered_under_each_insight(self):
        insights = [
            _make_insight(
                prose="Insight A",
                feature_type_id="reasoning_feature",
                semantic_category="analytical_reasoning",
            ),
            _make_insight(
                prose="Insight B",
                feature_type_id="communication_feature",
                semantic_category="communication_clarity",
            ),
        ]
        html = render_narrative({"narrative_insights": insights})
        assert html.count("Evidence:") == 2
        assert "Reasoning Feature" in html
        assert "Communication Feature" in html

    def test_missing_source_feature_id_fails_fast(self):
        class _BrokenInsight:
            insight_type = "strength_signal"
            prose = "Broken"
            confidence = 0.5
            source_feature_id = None
            is_traceable = True

        with pytest.raises(ValueError, match="source_feature_id"):
            render_narrative({"narrative_insights": [_BrokenInsight()]})

    def test_missing_is_traceable_fails_fast(self):
        class _BrokenIdentity:
            feature_type_id = "reasoning_feature"
            semantic_category = "analytical_reasoning"

        class _BrokenInsight:
            insight_type = "strength_signal"
            prose = "Broken"
            confidence = 0.5
            source_feature_id = _BrokenIdentity()
            is_traceable = None

        with pytest.raises(ValueError, match="is_traceable"):
            render_narrative({"narrative_insights": [_BrokenInsight()]})
