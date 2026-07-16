# app/ui/replay/panels/replay_coaching_panel.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.contracts.coaching.learning_objective import LearningObjective
from domain.contracts.coaching.study_recommendation import StudyRecommendation
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.replay.replay_session import ReplaySession


@dataclass(frozen=True)
class CoachingViewModel:
    """C-08 rendering model (EPIC-04-DATA-MODEL §4.8)."""

    section_a_label: str
    section_b_label: str
    overview_label: str
    narrative_insights: tuple[NarrativeInsight, ...]
    narrative_empty_label: Optional[str]
    overview_section: Optional[NarrativeSection]
    overview_prose: Optional[str]
    coaching_objectives: tuple[LearningObjective, ...]
    coaching_empty_label: Optional[str]
    coaching_recommendations: tuple[StudyRecommendation, ...]


class ReplayCoachingPanel:
    """C-08: narrative insights (A) and coaching study plan (B)."""

    SECTION_A_LABEL = "Session Narrative"
    SECTION_B_LABEL = "Study Plan"
    OVERVIEW_LABEL = "Knowledge Overview"
    NARRATIVE_EMPTY = "No narrative insights recorded"
    COACHING_EMPTY = "No coaching objectives recorded"

    def __init__(self, session: ReplaySession) -> None:
        self._session = session

    def render(self) -> CoachingViewModel:
        narrative = self._session.narrative
        coaching = self._session.coaching_snapshot

        insights = narrative.insights
        narrative_empty = self.NARRATIVE_EMPTY if not insights else None

        overview = narrative.overview_section
        overview_prose = overview.prose if overview is not None else None

        objectives = coaching.collection.objectives
        coaching_empty = self.COACHING_EMPTY if not objectives else None
        recommendations = coaching.collection.recommendations

        return CoachingViewModel(
            section_a_label=self.SECTION_A_LABEL,
            section_b_label=self.SECTION_B_LABEL,
            overview_label=self.OVERVIEW_LABEL,
            narrative_insights=insights,
            narrative_empty_label=narrative_empty,
            overview_section=overview,
            overview_prose=overview_prose,
            coaching_objectives=objectives,
            coaching_empty_label=coaching_empty,
            coaching_recommendations=recommendations,
        )
