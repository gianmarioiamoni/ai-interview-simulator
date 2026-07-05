# tests/ui/views/report/test_narrative_section.py
# EPIC-V13-05 Phase 10 — render_narrative section tests.

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType

from app.ui.views.report.sections.narrative_section import render_narrative


def _make_insight(
    prose: str = "Candidate shows strong reasoning.",
    insight_type: NarrativeInsightType = NarrativeInsightType.STRENGTH_SIGNAL,
    confidence: float = 0.85,
) -> NarrativeInsight:
    return NarrativeInsight(
        insight_type=insight_type,
        prose=prose,
        source_feature_id=FeatureIdentity.for_type(FeatureType.REASONING),
        confidence=confidence,
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
        insight = _make_insight(insight_type=NarrativeInsightType.STRENGTH_SIGNAL)
        html = render_narrative({"narrative_insights": [insight]})
        assert "Strength" in html

    def test_renders_risk_signal_label(self):
        insight = _make_insight(insight_type=NarrativeInsightType.RISK_SIGNAL)
        html = render_narrative({"narrative_insights": [insight]})
        assert "Risk" in html

    def test_renders_confidence(self):
        insight = _make_insight(confidence=0.72)
        html = render_narrative({"narrative_insights": [insight]})
        assert "72%" in html

    def test_renders_multiple_insights(self):
        insights = [
            _make_insight(prose="Insight A"),
            _make_insight(prose="Insight B", insight_type=NarrativeInsightType.GROWTH_OPPORTUNITY),
        ]
        html = render_narrative({"narrative_insights": insights})
        assert "Insight A" in html
        assert "Insight B" in html

    def test_section_header_present(self):
        insight = _make_insight()
        html = render_narrative({"narrative_insights": [insight]})
        assert "Narrative Insights" in html
