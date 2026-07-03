# app/graph/nodes/session_close_node.py
"""SessionCloseNode — MIG-04, RS-02B (PAT-06: LangGraph sole orchestrator).

Responsibilities (orchestration only):
1. Idempotency guard: return immediately if state.session_history is not None.
2. Read ProfileFeature[] from state.candidate_profile_v2.features (RS-02A).
3. Assemble KnowledgeSnapshot via KnowledgeSnapshotBuilder.
4. Assemble SessionCloseContext from InterviewState fields.
5. Run SessionClosePipeline.run(context) — sole invocation per session.
6. Write state.session_history on success.

RS-02B: KnowledgePipeline is NOT executed here. Features come from
state.candidate_profile_v2.features, populated by FeatureEngine in Phase D
of the reasoner cycle (ADS-01 Strategy A, ADR-018, ADR-020).

Sole writer: this node only. SessionClosePipeline never writes state.
"""

from __future__ import annotations

from domain.contracts.coaching.coaching_builder import CoachingBuilder
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.interview_state import InterviewState
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import PolicyVersions
from domain.contracts.knowledge_snapshot.knowledge_snapshot_builder import KnowledgeSnapshotBuilder
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy
from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    TranscriptEntry,
)
from services.session_close.session_close_context import SessionCloseContext
from services.session_close.session_close_pipeline import SessionClosePipeline
from app.core.logger import get_logger

logger = get_logger(__name__)

# ------------------------------------------------------------------
# Policy constants (PAT-04: frozen at MIG-04 baseline)
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

    coaching_snapshot = CoachingBuilder.empty(
        session_id=session_id,
        question_index=state.current_question_index,
    )

    narrative = _build_stub_narrative()

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


def _build_stub_narrative():
    """Build a minimal structural Narrative (no LLM — structural placeholder)."""
    from domain.contracts.feature.feature_identity import FeatureIdentity
    from domain.contracts.feature.feature_type import FeatureType

    stub_ref = (FeatureIdentity.for_type(FeatureType.REASONING),)

    def _section(section_type: NarrativeSectionType) -> NarrativeSection:
        return NarrativeSection(
            section_type=section_type,
            prose="Session closed.",
            feature_references=stub_ref,
            confidence_context="Structural placeholder — no LLM narrative generated.",
        )

    return (
        NarrativeBuilder()
        .with_executive_summary(_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
        .with_strengths(_section(NarrativeSectionType.STRENGTHS))
        .with_weaknesses(_section(NarrativeSectionType.WEAKNESSES))
        .with_growth_areas(_section(NarrativeSectionType.GROWTH))
        .with_recommendations(_section(NarrativeSectionType.RECOMMENDATIONS))
        .build()
    )


def _build_language_profile(session_id: str) -> LanguageProfile:
    """Build a minimal SINGLE-mode LanguageProfile for the session.

    V1.2 gap: LanguageProfile is not tracked on InterviewState.
    A default Python profile is used as the structural placeholder.
    MIG-05+ will derive this from session config.
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
