# app/graph/nodes/session_close_node.py
"""SessionCloseNode (PAT-06: LangGraph sole orchestrator).

Responsibilities (orchestration only):
1. Idempotency guard: return immediately if state.session_history is not None.
2. Read ProfileFeature[] from state.candidate_profile_v2.features.
3. Generate Narrative via NarrativeGenerator (sole Narrative producer).
4. Generate CoachingSnapshot via CoachingEngine (sole CoachingSnapshot producer).
5. Assemble KnowledgeSnapshot via KnowledgeSnapshotBuilder.
6. Assemble SessionCloseContext from InterviewState fields.
7. Run SessionClosePipeline.run(context) — sole invocation per session.
8. Write state.session_history on success.

KnowledgePipeline is NOT executed here. Features come from
state.candidate_profile_v2.features (ADR-018, ADR-020).

NarrativeGenerator failure falls back to structural stub.
CoachingEngine failure falls back to CoachingBuilder.empty().

Sole writer: this node only. SessionClosePipeline never writes state.
"""

from __future__ import annotations

from domain.contracts.coaching.coaching_builder import CoachingBuilder
from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.interview.generation_metadata import GenerationMetadata
from domain.contracts.interview_state import InterviewState
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.session_history.question_result_record import QuestionResultRecord
from domain.contracts.knowledge_snapshot.knowledge_snapshot import PolicyVersions
from domain.contracts.knowledge_snapshot.knowledge_snapshot_builder import KnowledgeSnapshotBuilder
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy
from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.interview.interview_cost_metrics import InterviewCostMetrics
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    TranscriptEntry,
)
from domain.profile.candidate_profile_builder import CandidateProfileBuilder
from services.coaching_engine.coaching_context import CoachingContext
from services.coaching_engine.coaching_engine import CoachingEngine
from services.narrative_generator.narrative_generation_context import NarrativeGenerationContext
from services.narrative_generator.narrative_generator import NarrativeGenerator
from services.session_close.session_close_context import SessionCloseContext
from services.session_close.session_close_pipeline import SessionClosePipeline
from app.core.logger import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------
# Policy constants
# ------------------------------------------------------------------
_POLICY_VERSIONS = PolicyVersions(
    feature_engine_version="1.0",
    language_policy_version="1.0",
    ttl_policy_version="1.0",
    evaluation_policy_version="1.0",
    narrative_schema_version="1.0",
    coaching_schema_version="1.0",
    profile_schema_version="1.0",
)

# Singleton pipeline — stateless, safe to share (ADR-022).
_pipeline = SessionClosePipeline()

# Singleton NarrativeGenerator — stateless, safe to share.
_narrative_generator = NarrativeGenerator()

# Singleton CoachingEngine — stateless, safe to share.
_coaching_engine = CoachingEngine()

# Default coding language when no LanguageProfile exists on state (V1.2 gap).
_DEFAULT_LANG = ProgrammingLanguage(
    language_id="python",
    display_name="Python",
    language_version="3.12",
    language_family="python",
)


# ------------------------------------------------------------------
# Node
# ------------------------------------------------------------------


def session_close_node(state: InterviewState) -> InterviewState:
    """Execute session close pipeline. Sole writer of state.session_history.

    Idempotency: returns state unchanged if session_history is already set.
    Non-fatal: any failure logs a warning and returns state with session_history=None.
    """
    if state.session_history is not None:
        logger.debug("session_close_node: session_history already set — skipping (idempotency)")
        return state

    try:
        candidate_identity_id = state.candidate_identity_id or state.interview_id
        session_id = state.interview_id

        knowledge_snapshot = _build_knowledge_snapshot(state, session_id, candidate_identity_id)
        context = _build_context(state, session_id, candidate_identity_id, knowledge_snapshot)

        result = _pipeline.run(context)

        if result.is_successful:
            logger.info(
                "session_close_node completed | session=%s candidate=%s",
                session_id,
                candidate_identity_id,
            )
            return state.model_copy(update={"session_history": result.session_history})

        logger.warning(
            "session_close_node pipeline failed — session_history not set | "
            "session=%s reason=%s",
            session_id,
            result.failure_reason,
        )
        return state

    except Exception as exc:
        logger.warning(
            "session_close_node exception — session_history not set | "
            "session=%s error=%s",
            state.interview_id,
            type(exc).__name__,
        )
        return state


# ------------------------------------------------------------------
# Assembly helpers
# ------------------------------------------------------------------


def _build_knowledge_snapshot(
    state: InterviewState,
    session_id: str,
    candidate_identity_id: str,
):
    """Assemble KnowledgeSnapshot from state artifacts (KnowledgeSnapshotBuilder sole path).

    RS-02B: features come from state.candidate_profile_v2.features (ADS-01 Strategy A).
    No KnowledgePipeline execution at close time.
    """
    features: tuple[ProfileFeature, ...] = (
        state.candidate_profile_v2.features
        if state.candidate_profile_v2 is not None
        else ()
    )
    profile_snapshot = CandidateProfileSnapshot(
        candidate_identity_id=candidate_identity_id,
        features=features,
        closed_at_question_index=state.current_question_index,
        source_observation_ids=_collect_observation_ids(state),
        total_feature_count=len(features),
        mean_confidence=_mean_confidence(features),
    )

    coaching_snapshot = _generate_coaching_snapshot(
        state=state,
        features=features,
        session_id=session_id,
        candidate_identity_id=candidate_identity_id,
    )

    narrative = _generate_narrative(
        state=state,
        features=features,
        session_id=session_id,
        candidate_identity_id=candidate_identity_id,
    )

    return (
        KnowledgeSnapshotBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_identity_id)
        .with_profile_snapshot(profile_snapshot)
        .with_narrative(narrative)
        .with_coaching_snapshot(coaching_snapshot)
        .with_policy_versions(_POLICY_VERSIONS)
        .build()
    )


def _build_context(
    state: InterviewState,
    session_id: str,
    candidate_identity_id: str,
    knowledge_snapshot,
) -> SessionCloseContext:
    interview_metadata = InterviewMetadata(
        role=str(state.role.type.value),
        seniority=state.seniority_level,
        interview_type=state.interview_type.value,
        interview_mode=_resolve_interview_mode(state),
        session_language=state.language,
        question_count=max(len(state.questions), 1),
        company=state.company or None,
    )

    language_profile = _build_language_profile(session_id)

    transcript = _build_transcript(state)
    question_timeline = _build_question_timeline(state)

    question_results = _build_question_results(state)
    generation_metadata = _build_generation_metadata(state)

    return SessionCloseContext(
        session_id=session_id,
        candidate_identity_id=candidate_identity_id,
        interview_index=0,
        knowledge_snapshot=knowledge_snapshot,
        interview_metadata=interview_metadata,
        language_profile=language_profile,
        transcript=tuple(transcript),
        question_timeline=tuple(question_timeline),
        evaluation_result=state.interview_evaluation,
        scoring_snapshot=state.scoring_snapshot,
        scoring_narrative=state.scoring_narrative,
        question_results=tuple(question_results),
        context_profile=state.context_profile if state.context_profile else None,
        generation_metadata=generation_metadata,
    )


# ------------------------------------------------------------------
# Domain helpers (pure functions, no side effects)
# ------------------------------------------------------------------


def _collect_observation_ids(state: InterviewState) -> tuple[str, ...]:
    """Collect observation IDs from observation_store for provenance."""
    store = state.observation_store
    if store is None:
        return ()
    try:
        snap = store.snapshot()
        return tuple(obs.observation_id for obs in snap.observations)
    except Exception:
        return ()


def _mean_confidence(features: tuple) -> float:
    if not features:
        return 0.0
    return sum(f.quality.confidence.value for f in features) / len(features)


def _generate_narrative(
    state: InterviewState,
    features: tuple[ProfileFeature, ...],
    session_id: str,
    candidate_identity_id: str,
) -> Narrative:
    """Generate Narrative via NarrativeGenerator (sole Narrative producer).

    Builds NarrativeGenerationContext from available state artifacts without
    invoking FeatureEngine, KnowledgePipeline, or ObservationExtractor.
    Falls back to structural stub on any failure (non-fatal; close always succeeds).
    """
    try:
        profile = state.candidate_profile_v2 or CandidateProfileBuilder().build()
        feature_collection = FeatureCollection.from_iterable(list(features))
        ctx = NarrativeGenerationContext(
            session_id=session_id,
            candidate_identity_id=candidate_identity_id,
            question_index=state.current_question_index,
            profile=profile,
            features=feature_collection,
        )
        result = _narrative_generator.generate(ctx)
        if result.is_successful and result.narrative is not None:
            logger.debug(
                "_generate_narrative succeeded | session=%s features=%d insights=%d",
                session_id,
                feature_collection.size,
                result.narrative.insight_count,
            )
            return result.narrative
        logger.warning(
            "_generate_narrative unsuccessful — using stub | session=%s reason=%s",
            session_id,
            result.failure_reason,
        )
    except Exception as exc:
        logger.warning(
            "_generate_narrative exception — using stub | session=%s error=%s",
            session_id,
            type(exc).__name__,
        )
    return _build_stub_narrative()


def _build_stub_narrative() -> Narrative:
    """Minimal structural Narrative — fallback only when NarrativeGenerator fails."""
    from domain.contracts.feature.feature_identity import FeatureIdentity
    from domain.contracts.feature.feature_type import FeatureType

    stub_ref = (FeatureIdentity.for_type(FeatureType.REASONING),)

    def _section(section_type: NarrativeSectionType) -> NarrativeSection:
        return NarrativeSection(
            section_type=section_type,
            prose="Session closed.",
            feature_references=stub_ref,
            confidence_context="Fallback — NarrativeGenerator unavailable.",
        )

    return (
        NarrativeBuilder()
        .with_overview_section(_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
        .with_strengths(_section(NarrativeSectionType.STRENGTHS))
        .with_weaknesses(_section(NarrativeSectionType.WEAKNESSES))
        .with_growth_areas(_section(NarrativeSectionType.GROWTH))
        .with_recommendations(_section(NarrativeSectionType.RECOMMENDATIONS))
        .build()
    )


def _generate_coaching_snapshot(
    state: InterviewState,
    features: tuple[ProfileFeature, ...],
    session_id: str,
    candidate_identity_id: str,
) -> "CoachingSnapshot":
    """Generate CoachingSnapshot via CoachingEngine (sole CoachingSnapshot producer).

    Builds CoachingContext from available state artifacts without invoking
    FeatureEngine, KnowledgePipeline, or ObservationExtractor.
    Falls back to CoachingBuilder.empty() on failure (non-fatal; close always succeeds).
    """
    try:
        profile = state.candidate_profile_v2 or CandidateProfileBuilder().build()
        ctx = CoachingContext(
            session_id=session_id,
            candidate_identity_id=candidate_identity_id,
            question_index=state.current_question_index,
            profile=profile,
            features=features,
            interview_role=str(state.role.type.value),
            interview_topic=state.interview_type.value,
        )
        result = _coaching_engine.run(ctx)
        if result.is_successful:
            logger.debug(
                "_generate_coaching_snapshot succeeded | session=%s objectives=%d",
                session_id,
                result.objective_count,
            )
            return result.snapshot
        logger.warning(
            "_generate_coaching_snapshot unsuccessful — using empty | session=%s reason=%s",
            session_id,
            result.failure_reason,
        )
    except Exception as exc:
        logger.warning(
            "_generate_coaching_snapshot exception — using empty | session=%s error=%s",
            session_id,
            type(exc).__name__,
        )
    return CoachingBuilder.empty(session_id=session_id, question_index=state.current_question_index)


def _build_language_profile(session_id: str) -> LanguageProfile:
    """Build a minimal SINGLE-mode LanguageProfile for the session.

    LanguageProfile is not tracked on InterviewState; a default Python profile
    is used as the structural placeholder.
    """
    return LanguageProfile(
        session_id=session_id,
        session_mode=SessionMode.SINGLE,
        primary_language=_DEFAULT_LANG,
        active_languages=[_DEFAULT_LANG],
        selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
        language_sequence=["python"],
        execution_policies=[ExecutionPolicy(language_id="python")],
        language_policies=[LanguagePolicy(language_id="python", policy_version="1.0")],
    )


def _resolve_interview_mode(state: InterviewState) -> str:
    """Derive interview_mode from question types present in the session."""
    from domain.contracts.question.question import QuestionType
    types = {q.type for q in state.questions}
    if QuestionType.WRITTEN in types and QuestionType.CODING in types:
        return "mixed"
    if QuestionType.WRITTEN in types:
        return "written"
    return "coding"


def _build_transcript(state: InterviewState) -> list[TranscriptEntry]:
    """Build transcript from matched question/answer pairs."""
    entries: list[TranscriptEntry] = []
    for idx, question in enumerate(state.questions):
        answer = next(
            (a for a in state.answers if a.question_id == question.id),
            None,
        )
        if answer is None:
            continue
        entries.append(
            TranscriptEntry(
                question_index=idx,
                question_id=question.id,
                question_prompt=question.prompt,
                answer_content=answer.content,
                answer_attempt=answer.attempt,
            )
        )
    return entries


def _build_question_timeline(state: InterviewState) -> list[QuestionTimelineEntry]:
    """Build question timeline from questions present in state."""
    return [
        QuestionTimelineEntry(
            question_index=idx,
            question_id=q.id,
            question_type=q.type.value,
            question_difficulty=q.difficulty.value,
        )
        for idx, q in enumerate(state.questions)
    ]


def _build_question_results(state: InterviewState) -> list[QuestionResultRecord]:
    """Build QuestionResultRecord list from state (Phase 7B, ADR-033).

    Constructs one record per answered question that has an evaluation.
    Fields are sourced directly from QuestionResult — no recomputation.
    """
    from app.ui.mappers.interview_area_mapper import InterviewAreaMapper

    records: list[QuestionResultRecord] = []
    for idx, question in enumerate(state.questions):
        result = state.results_by_question.get(question.id)
        if result is None:
            continue
        evaluation = result.evaluation
        if evaluation is None:
            continue

        attempts = sum(
            1 for a in state.answers if a.question_id == question.id
        ) or 1

        execution = result.execution
        passed_tests: int | None = None
        total_tests: int | None = None
        execution_status: str | None = None
        if execution is not None:
            passed_tests = getattr(execution, "passed_tests", None)
            total_tests = getattr(execution, "total_tests", None)
            execution_status = getattr(execution, "status", None)
            if hasattr(execution_status, "value"):
                execution_status = execution_status.value

        hint = getattr(result, "ai_hint", None)
        ai_hint_explanation: str | None = getattr(hint, "explanation", None) if hint else None
        ai_hint_suggestion: str | None = getattr(hint, "suggestion", None) if hint else None

        try:
            area_label = InterviewAreaMapper.to_label(question.area)
        except Exception:
            area_label = question.area.value if hasattr(question.area, "value") else str(question.area)

        strengths: tuple[str, ...] = tuple(getattr(evaluation, "strengths", None) or ())
        weaknesses: tuple[str, ...] = tuple(getattr(evaluation, "weaknesses", None) or ())
        follow_up_question: str | None = getattr(evaluation, "follow_up_question", None)

        records.append(
            QuestionResultRecord(
                question_id=question.id,
                question_index=idx,
                question_type=question.type.value,
                area_label=area_label,
                question_prompt=question.prompt,
                score=evaluation.score,
                max_score=evaluation.max_score,
                feedback=evaluation.feedback,
                strengths=strengths,
                weaknesses=weaknesses,
                follow_up_question=follow_up_question,
                passed_tests=passed_tests,
                total_tests=total_tests,
                execution_status=execution_status,
                attempts=attempts,
                ai_hint_explanation=ai_hint_explanation,
                ai_hint_suggestion=ai_hint_suggestion,
            )
        )
    return records


def _build_generation_metadata(state: InterviewState) -> GenerationMetadata | None:
    """Build GenerationMetadata from cost metrics already on state (Phase 7B, ADR-033).

    Uses state.interview_cost_metrics if available. No recomputation.
    """
    cost: InterviewCostMetrics | None = state.interview_cost_metrics
    if cost is None:
        return None

    metrics = state.interview_metrics
    total_tokens = getattr(metrics, "total_tokens", 0) if metrics is not None else 0

    return GenerationMetadata(
        total_tokens_used=total_tokens,
        total_cost_usd=cost.total_cost_usd,
        cost_per_question_usd=cost.cost_per_question_usd,
    )
