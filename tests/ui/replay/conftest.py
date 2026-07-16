# tests/ui/replay/conftest.py

from __future__ import annotations

from datetime import datetime, timezone

from domain.contracts.coaching.coaching_builder import CoachingBuilder, CoachingSnapshot
from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import ResourceType, StudyRecommendation
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_manifest import ReplayManifest, ReplaySourcePriority
from domain.contracts.replay.replay_question_record import ReplayQuestionRecord
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata
from domain.contracts.replay.replay_timeline import ReplayTimeline, ReplayTimelineEntry
from domain.contracts.report.scoring_dimension import ScoringDimension
from domain.contracts.report.scoring_snapshot import ScoringSnapshot
from domain.contracts.report.scoring_snapshot_builder import ScoringSnapshotBuilder
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    REASONING_IDENTITY,
    SESSION_ID,
    make_candidate_profile_snapshot,
    make_coaching_snapshot,
    make_narrative,
    make_policy_versions,
    make_section,
)

SESSION_DATE = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)


def make_question_record(
    *,
    index: int = 0,
    candidate_answer: str = "Answer text",
    strengths: tuple[str, ...] = ("Clear structure",),
    weaknesses: tuple[str, ...] = ("Missed edge cases",),
    follow_up_question: str | None = "Can you elaborate?",
    ai_hint_explanation: str | None = "Think about complexity.",
    ai_hint_suggestion: str | None = "Use a hash map.",
    execution_status: str | None = None,
    passed_tests: int | None = None,
    total_tests: int | None = None,
) -> ReplayQuestionRecord:
    return ReplayQuestionRecord(
        question_id=f"q-{index:03d}",
        question_index=index,
        question_type="coding" if execution_status is not None else "technical",
        area_label="Algorithms",
        question_prompt=f"Prompt {index}",
        candidate_answer=candidate_answer,
        score=70.0,
        max_score=100.0,
        feedback="Solid approach.",
        strengths=strengths,
        weaknesses=weaknesses,
        follow_up_question=follow_up_question,
        ai_hint_explanation=ai_hint_explanation,
        ai_hint_suggestion=ai_hint_suggestion,
        execution_status=execution_status,
        passed_tests=passed_tests,
        total_tests=total_tests,
        attempts=1,
    )


def make_scoring_snapshot(*, gating_triggered: bool = False) -> ScoringSnapshot:
    dimensions = (
        ScoringDimension(
            dimension_type=PerformanceDimensionType.TECHNICAL_DEPTH,
            score=75.0,
            signal=0.8,
            weighted_contribution=0.3,
            justification="Good technical depth.",
            level="strong",
        ),
        ScoringDimension(
            dimension_type=PerformanceDimensionType.PROBLEM_SOLVING,
            score=60.0,
            signal=0.6,
            weighted_contribution=0.25,
            justification="Adequate problem solving.",
            level="moderate",
        ),
    )
    builder = (
        ScoringSnapshotBuilder()
        .with_overall_score(72.5)
        .with_scoring_dimensions(dimensions)
        .with_level(InterviewLevel.STRONG)
        .with_hire_decision(HireDecision.HIRE)
        .with_hiring_probability(78.0)
        .with_percentile_rank(65.0)
        .with_percentile_explanation("Better than 65% of candidates.")
        .with_decision_explanation(
            {"strengths": ["Good problem solving"], "gaps": ["System design"]}
        )
        .with_confidence(Confidence(base=0.85, final=0.80))
    )
    if gating_triggered:
        builder = builder.with_gating(triggered=True, reason="Integrity check failed")
    else:
        builder = builder.with_gating(triggered=False)
    return builder.build()


def make_narrative_with_insights() -> Narrative:
    insight = NarrativeInsight(
        insight_type=NarrativeInsightType.STRENGTH_SIGNAL,
        prose="Candidate showed strong reasoning.",
        source_feature_id=REASONING_IDENTITY,
        confidence=0.85,
    )
    return (
        NarrativeBuilder()
        .with_overview_section(make_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
        .with_strengths(make_section(NarrativeSectionType.STRENGTHS))
        .with_weaknesses(make_section(NarrativeSectionType.WEAKNESSES))
        .with_growth_areas(make_section(NarrativeSectionType.GROWTH))
        .with_recommendations(make_section(NarrativeSectionType.RECOMMENDATIONS))
        .with_insight(insight)
        .build()
    )


def make_populated_coaching_snapshot() -> CoachingSnapshot:
    objective = LearningObjective(
        objective_id="obj-1",
        feature_type=FeatureType.REASONING,
        description="Strengthen algorithmic reasoning",
        priority=ObjectivePriority.HIGH,
        confidence=0.9,
        supporting_observation_types=(ObservationType.REASONING_DEPTH_LOW,),
        detected_at_question_index=0,
        candidate_identity_id=CANDIDATE_ID,
    )
    recommendation = StudyRecommendation(
        recommendation_id="rec-1",
        objective_id=objective.objective_id,
        resource_type=ResourceType.EXERCISE,
        topic="Hash maps",
        rationale="Addresses lookup complexity gaps",
        estimated_duration_hours=2.0,
    )
    return CoachingBuilder.build(
        objectives=(objective,),
        actions=(),
        recommendations=(recommendation,),
        session_id=SESSION_ID,
        question_index=0,
    )


def make_replay_session(
    *,
    question_results: tuple[ReplayQuestionRecord, ...] | None = None,
    scoring_snapshot: ScoringSnapshot | None = None,
    coaching_snapshot: CoachingSnapshot | None = None,
    narrative: Narrative | None = None,
    is_successful: bool = True,
    failure_reason: str | None = None,
    session_duration_seconds: float | None = 120.0,
    company: str | None = "Acme Corp",
) -> ReplaySession:
    records = question_results if question_results is not None else (make_question_record(),)
    question_count = len(records)

    if question_count == 0:
        timeline = ReplayTimeline(
            entries=(),
            total_positions=0,
            first_position=-1,
            last_position=-1,
            is_empty=True,
        )
    else:
        entries = tuple(
            ReplayTimelineEntry(
                position=i,
                question_id=records[i].question_id,
                question_index=i,
                area_label=records[i].area_label,
                question_type=records[i].question_type,
            )
            for i in range(question_count)
        )
        timeline = ReplayTimeline(
            entries=entries,
            total_positions=question_count,
            first_position=0,
            last_position=question_count - 1,
            is_empty=False,
        )

    if not is_successful and failure_reason is None:
        failure_reason = "SessionHistory not found"
    if is_successful:
        failure_reason = None

    return ReplaySession(
        session_id=SESSION_ID,
        candidate_identity_id=CANDIDATE_ID,
        profile_snapshot=make_candidate_profile_snapshot(),
        narrative=narrative if narrative is not None else make_narrative(),
        coaching_snapshot=(
            coaching_snapshot if coaching_snapshot is not None else make_coaching_snapshot()
        ),
        scoring_snapshot=scoring_snapshot,
        policy_versions=make_policy_versions(),
        knowledge_epoch="1",
        manifest=ReplayManifest.for_standard_replay(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            replay_level=ReplayLevel.PRESENTATION,
            replay_engine_version="1.0",
            source_per_component={
                "profile": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
                "narrative": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
                "coaching": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
                "policy_versions": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            },
        ),
        session_metadata=ReplaySessionMetadata(
            interview_index=1,
            session_date=SESSION_DATE,
            role="Software Engineer",
            seniority_level="Senior",
            interview_mode="technical",
            question_count=question_count,
            session_duration_seconds=session_duration_seconds,
            company=company,
        ),
        timeline=timeline,
        question_results=records,
        is_successful=is_successful,
        failure_reason=failure_reason,
        replay_mode=ReplayMode.STANDARD,
        replay_level=ReplayLevel.PRESENTATION,
    )
