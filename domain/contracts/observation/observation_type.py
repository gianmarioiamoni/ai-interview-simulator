# domain/contracts/observation/observation_type.py
# ADR-016: Observation schema & ObservationType registry
# ADR-066: Behavioral Observation Model migration contract

from enum import Enum


class ObservationType(str, Enum):
    """Taxonomy of typed observations produced by ObservationExtractor.

    Immutable registry — new types are additions only; no renames or removals
    without a deprecation ADR (ADR-016, ADR-066).

    Categories:
        TECHNICAL_*      — code correctness, depth, quality signals
        REASONING_*      — causal analysis and trade-off quality
        COMMUNICATION_*  — clarity and structure of verbal/written output
        CONFIDENCE_*     — self-assessment calibration signals
        BEHAVIORAL_*     — soft-skill and inter-personal patterns
        KNOWLEDGE_*      — domain knowledge gaps and coverage
        PERFORMANCE_*    — cross-session trend and growth signals
    """

    # --- Technical ---
    TECHNICAL_CORRECTNESS = "technical_correctness"
    TECHNICAL_DEPTH = "technical_depth"
    TECHNICAL_SHALLOW = "technical_shallow"
    TECHNICAL_GAP = "technical_gap"
    TECHNICAL_STRENGTH = "technical_strength"
    TECHNICAL_RECOVERED = "technical_recovered"

    # --- Reasoning ---
    REASONING_DEPTH_HIGH = "reasoning_depth_high"
    REASONING_DEPTH_LOW = "reasoning_depth_low"
    REASONING_IMPROVING = "reasoning_improving"
    REASONING_STAGNATING = "reasoning_stagnating"
    REASONING_CONTRADICTORY = "reasoning_contradictory"

    # --- Communication ---
    COMMUNICATION_CLEAR = "communication_clear"
    COMMUNICATION_WEAK = "communication_weak"
    COMMUNICATION_INCONSISTENT = "communication_inconsistent"
    COMMUNICATION_GAP = "communication_gap"

    # --- Confidence ---
    CONFIDENCE_WELL_CALIBRATED = "confidence_well_calibrated"
    CONFIDENCE_OVERCONFIDENT = "confidence_overconfident"
    CONFIDENCE_UNDERCONFIDENT = "confidence_underconfident"
    CONFIDENCE_UNSTABLE = "confidence_unstable"
    CONFIDENCE_SATURATED = "confidence_saturated"
    CONFIDENCE_DROP = "confidence_drop"

    # --- Behavioral: Leadership (DET-11, ADR-066) ---
    LEADERSHIP_STRONG = "leadership_strong"
    LEADERSHIP_EMERGING = "leadership_emerging"
    LEADERSHIP_ABSENT = "leadership_absent"

    # --- Behavioral: Collaboration (DET-12, ADR-066) ---
    COLLABORATION_STRONG = "collaboration_strong"
    COLLABORATION_EFFECTIVE = "collaboration_effective"
    COLLABORATION_DEFICIT = "collaboration_deficit"

    # --- Behavioral: Adaptability (DET-13, ADR-066) ---
    ADAPTABILITY_HIGH = "adaptability_high"
    ADAPTABILITY_MODERATE = "adaptability_moderate"
    ADAPTABILITY_LOW = "adaptability_low"

    # --- Behavioral: General ---
    BEHAVIORAL_GROWTH = "behavioral_growth"
    BEHAVIORAL_INSTABILITY = "behavioral_instability"
    BEHAVIORAL_PLATEAU = "behavioral_plateau"

    # --- Knowledge ---
    KNOWLEDGE_GAP = "knowledge_gap"
    KNOWLEDGE_DEMONSTRATED = "knowledge_demonstrated"
    KNOWLEDGE_CROSS_AREA_CONSISTENT = "knowledge_cross_area_consistent"
    KNOWLEDGE_CROSS_AREA_CONTRADICTORY = "knowledge_cross_area_contradictory"

    # --- Engineering judgment ---
    ENGINEERING_JUDGMENT_HIGH = "engineering_judgment_high"
    ENGINEERING_JUDGMENT_LOW = "engineering_judgment_low"
    ENGINEERING_JUDGMENT_ARTICULATED = "engineering_judgment_articulated"

    # --- Performance trends ---
    PERFORMANCE_IMPROVING = "performance_improving"
    PERFORMANCE_DECLINING = "performance_declining"
    PERFORMANCE_STABLE = "performance_stable"
