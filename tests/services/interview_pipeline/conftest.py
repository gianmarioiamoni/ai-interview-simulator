# tests/services/interview_pipeline/conftest.py
# Shared fixtures and stubs for InterviewPipeline test suite

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from domain.contracts.coaching.coaching_builder import CoachingBuilder, CoachingSnapshot
from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.coaching_engine.coaching_context import CoachingContext
from services.coaching_engine.coaching_diagnostics import (
    CoachingDiagnostics,
    CoachingStage,
    CoachingStageRecord,
)
from services.coaching_engine.coaching_engine import CoachingEngine
from services.coaching_engine.coaching_metrics import CoachingMetrics
from services.coaching_engine.coaching_result import CoachingResult
from services.interview_pipeline.interview_pipeline import InterviewPipeline
from services.interview_pipeline.interview_pipeline_configuration import (
    InterviewPipelineConfiguration,
)
from services.interview_pipeline.interview_pipeline_context import InterviewPipelineContext
from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
from services.knowledge_pipeline.knowledge_pipeline_diagnostics import (
    KnowledgePipelineDiagnostics,
    PipelineStage,
    StageAuditRecord as KpStageAuditRecord,
)
from services.knowledge_pipeline.knowledge_pipeline_metrics import KnowledgePipelineMetrics
from services.knowledge_pipeline.knowledge_pipeline_result import KnowledgePipelineResult
from services.narrative_generator.narrative_generation_diagnostics import (
    NarrativeGenerationDiagnostics,
    NarrativeStage,
    StageAuditRecord as NgStageAuditRecord,
)
from services.narrative_generator.narrative_generation_metrics import NarrativeGenerationMetrics
from services.narrative_generator.narrative_generation_result import NarrativeGenerationResult
from services.narrative_generator.narrative_generator import NarrativeGenerator
from services.session_close.session_close_pipeline import SessionClosePipeline

import uuid

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SESSION = "sess-001"
CAND = "cand-001"
Q_IDX = 3


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------

def make_candidate_profile(
    questions_answered: int = 3,
    areas: list[str] | None = None,
) -> CandidateProfile:
    return CandidateProfile(
        questions_answered=questions_answered,
        areas_covered=areas or ["algorithms"],
        last_updated_at_question_index=questions_answered - 1,
    )


def make_profile_feature(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
    question_index: int = 3,
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=FeatureQuality(
            confidence=FeatureConfidence(value=0.8),
            stability=FeatureStability(state="emerging"),
            maturity=FeatureMaturity.from_observation_count(2),
        ),
        provenance=FeatureProvenance(
            feature_identity=identity,
            source_observation_ids=(str(uuid.uuid4()),),
            computed_at_question_index=question_index,
            feature_engine_version="1.0.0",
            updater_id="stub-updater",
        ),
        computed_at_question_index=question_index,
        candidate_identity_id=CAND,
    )


def make_signal(
    question_index: int = 3,
    session_id: str = SESSION,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=question_index,
        timestamp_question_index=question_index,
        question_area="algorithms",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.POSITIVE,
        signal_type=EvidenceType.REPEATED_STRENGTH,
        strength=0.8,
        source=EvidenceSource.EVALUATION,
    )


# ---------------------------------------------------------------------------
# Stub sub-pipelines
# ---------------------------------------------------------------------------

def make_kp_result(
    session_id: str = SESSION,
    candidate_id: str = CAND,
    question_index: int = Q_IDX,
    is_successful: bool = True,
    profile: CandidateProfile | None = None,
    features: tuple[ProfileFeature, ...] | None = None,
    failure_reason: str | None = None,
) -> KnowledgePipelineResult:
    metrics = KnowledgePipelineMetrics(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
    )
    if is_successful:
        diagnostics = KnowledgePipelineDiagnostics.successful(
            session_id=session_id,
            candidate_identity_id=candidate_id,
            question_index=question_index,
            stage_records=(),
            metrics=metrics,
        )
    else:
        diagnostics = KnowledgePipelineDiagnostics.failed(
            session_id=session_id,
            candidate_identity_id=candidate_id,
            question_index=question_index,
            stage_records=(),
            metrics=metrics,
            failure_stage=PipelineStage.EXTRACTION,
            failure_reason=failure_reason or "stub failure",
        )
    return KnowledgePipelineResult(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
        profile=profile or (make_candidate_profile() if is_successful else None),
        features=features or ((make_profile_feature(),) if is_successful else ()),
        diagnostics=diagnostics,
        is_successful=is_successful,
        failure_reason=failure_reason,
    )


def make_ng_result(
    session_id: str = SESSION,
    candidate_id: str = CAND,
    question_index: int = Q_IDX,
    is_successful: bool = True,
    narrative: Narrative | None = None,
    failure_reason: str | None = None,
) -> NarrativeGenerationResult:
    metrics = NarrativeGenerationMetrics(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
        sections_built=3 if is_successful else 0,
        insights_built=2 if is_successful else 0,
    )
    if is_successful:
        diagnostics = NarrativeGenerationDiagnostics.successful(
            session_id=session_id,
            candidate_identity_id=candidate_id,
            question_index=question_index,
            stage_records=(),
            metrics=metrics,
        )
    else:
        diagnostics = NarrativeGenerationDiagnostics.failed(
            session_id=session_id,
            candidate_identity_id=candidate_id,
            question_index=question_index,
            stage_records=(),
            metrics=metrics,
            failure_stage=NarrativeStage.CONTEXT_VALIDATION,
            failure_reason=failure_reason or "stub narrative failure",
        )
    return NarrativeGenerationResult(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
        narrative=narrative,
        diagnostics=diagnostics,
        is_successful=is_successful,
        failure_reason=failure_reason,
    )


def make_ce_result(
    session_id: str = SESSION,
    candidate_id: str = CAND,
    question_index: int = Q_IDX,
    is_successful: bool = True,
    failure_reason: str | None = None,
) -> CoachingResult:
    snapshot = CoachingBuilder.empty(session_id=session_id, question_index=question_index)
    metrics = CoachingMetrics(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
    )
    records = [CoachingStageRecord(
        stage=CoachingStage.GAP_ANALYSIS,
        completed=is_successful,
        duration_ms=0.0,
    )]
    if is_successful:
        diag = CoachingDiagnostics.successful(
            session_id=session_id,
            candidate_identity_id=candidate_id,
            question_index=question_index,
            stage_records=tuple(records),
            metrics=metrics,
        )
    else:
        diag = CoachingDiagnostics.failed(
            session_id=session_id,
            candidate_identity_id=candidate_id,
            question_index=question_index,
            stage_records=tuple(records),
            metrics=metrics,
            failure_stage=CoachingStage.GAP_ANALYSIS,
            failure_reason=failure_reason or "stub coaching failure",
        )
    return CoachingResult(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
        snapshot=snapshot,
        diagnostics=diag,
        is_successful=is_successful,
        failure_reason=failure_reason,
    )


# ---------------------------------------------------------------------------
# Stub pipeline builders
# ---------------------------------------------------------------------------

class StubKnowledgePipeline:
    def __init__(self, result: KnowledgePipelineResult) -> None:
        self._result = result
        self.call_count = 0
        self.last_context = None

    def run(self, context: Any) -> KnowledgePipelineResult:
        self.call_count += 1
        self.last_context = context
        return self._result


class StubNarrativeGenerator:
    def __init__(self, result: NarrativeGenerationResult) -> None:
        self._result = result
        self.call_count = 0
        self.last_context = None

    def generate(self, context: Any) -> NarrativeGenerationResult:
        self.call_count += 1
        self.last_context = context
        return self._result


class StubCoachingEngine:
    def __init__(self, result: CoachingResult) -> None:
        self._result = result
        self.call_count = 0
        self.last_context = None

    def run(self, context: Any) -> CoachingResult:
        self.call_count += 1
        self.last_context = context
        return self._result


class RaisingKnowledgePipeline:
    def run(self, context: Any) -> Any:
        raise RuntimeError("knowledge pipeline explosion")


class RaisingNarrativeGenerator:
    def generate(self, context: Any) -> Any:
        raise RuntimeError("narrative generator explosion")


class RaisingCoachingEngine:
    def run(self, context: Any) -> Any:
        raise RuntimeError("coaching engine explosion")


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def make_pipeline(
    kp_result: KnowledgePipelineResult | None = None,
    ng_result: NarrativeGenerationResult | None = None,
    ce_result: CoachingResult | None = None,
    configuration: InterviewPipelineConfiguration | None = None,
    kp_stub: Any = None,
    ng_stub: Any = None,
    ce_stub: Any = None,
) -> tuple[InterviewPipeline, Any, Any, Any]:
    kp = kp_stub or StubKnowledgePipeline(kp_result or make_kp_result())
    ng = ng_stub or StubNarrativeGenerator(ng_result or make_ng_result())
    ce = ce_stub or StubCoachingEngine(ce_result or make_ce_result())
    sc = SessionClosePipeline()
    pipeline = InterviewPipeline(
        knowledge_pipeline=kp,  # type: ignore[arg-type]
        narrative_generator=ng,  # type: ignore[arg-type]
        coaching_engine=ce,  # type: ignore[arg-type]
        session_close_pipeline=sc,
        configuration=configuration,
    )
    return pipeline, kp, ng, ce


def make_context(
    session_id: str = SESSION,
    candidate_id: str = CAND,
    question_index: int = Q_IDX,
    signals: tuple[EvidenceSignal, ...] | None = None,
    prior_profile: CandidateProfile | None = None,
    interview_topic: str | None = "algorithms",
    interview_role: str | None = "Senior Engineer",
) -> InterviewPipelineContext:
    return InterviewPipelineContext(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
        signals=signals if signals is not None else (make_signal(question_index=question_index),),
        prior_profile=prior_profile,
        interview_topic=interview_topic,
        interview_role=interview_role,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session_id() -> str:
    return SESSION


@pytest.fixture
def candidate_id() -> str:
    return CAND


@pytest.fixture
def base_context() -> InterviewPipelineContext:
    return make_context()


@pytest.fixture
def successful_pipeline():
    pipeline, kp, ng, ce = make_pipeline()
    return pipeline, kp, ng, ce
