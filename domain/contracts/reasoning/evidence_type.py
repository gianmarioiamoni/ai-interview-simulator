# domain/contracts/reasoning/evidence_type.py

from enum import Enum


class EvidenceType(str, Enum):
    # --- Positive ---
    REPEATED_STRENGTH = "repeated_strength"
    RECOVERED_WEAKNESS = "recovered_weakness"
    DEMONSTRATED_DEPTH = "demonstrated_depth"
    ENGINEERING_JUDGMENT_ARTICULATED = "engineering_judgment_articulated"

    # --- Negative ---
    REPEATED_WEAKNESS = "repeated_weakness"
    KNOWLEDGE_GAP = "knowledge_gap"
    COMMUNICATION_GAP = "communication_gap"
    REASONING_GAP = "reasoning_gap"
    CONFIDENCE_DROP = "confidence_drop"
    MISSING_EVIDENCE = "missing_evidence"
    SHALLOW_ANSWER = "shallow_answer"
    CONTRADICTORY_ANSWER = "contradictory_answer"

    # --- Reasoning depth (M2-7B) ---
    REASONING_DEPTH_HIGH = "reasoning_depth_high"      # deep causal / trade-off reasoning
    REASONING_DEPTH_LOW = "reasoning_depth_low"        # surface-level / memorised answers
    REASONING_IMPROVING = "reasoning_improving"        # depth trend is upward
    REASONING_STAGNATING = "reasoning_stagnating"      # depth not improving despite multiple signals

    # --- Engineering judgment (M2-7C) ---
    ENGINEERING_JUDGMENT_HIGH = "engineering_judgment_high"    # strong trade-off / operational reasoning
    ENGINEERING_JUDGMENT_LOW = "engineering_judgment_low"      # shallow judgment dimension

    # --- Communication quality (M2-7C) ---
    COMMUNICATION_CLEAR = "communication_clear"                # consistent clear communication
    COMMUNICATION_WEAK = "communication_weak"                  # persistent communication weakness
    COMMUNICATION_INCONSISTENT = "communication_inconsistent"  # inconsistent communication signals

    # --- Behavioral patterns (M2-7D) ---
    BEHAVIORAL_GROWTH = "behavioral_growth"            # confidence / competence growing over time
    BEHAVIORAL_INSTABILITY = "behavioral_instability"  # inconsistent attitude / erratic answers
    BEHAVIORAL_PLATEAU = "behavioral_plateau"          # stable but not improving over time

    # --- Cross-interview consistency (M2-7D) ---
    CROSS_AREA_CONSISTENT = "cross_area_consistent"    # consistent performance across question areas
    CROSS_AREA_CONTRADICTORY = "cross_area_contradictory"  # contradictory performance across areas

    # --- Leadership (M2-7H, DET-11) ---
    LEADERSHIP_STRONG   = "LEADERSHIP_STRONG"    # strong multi-dimension leadership signals
    LEADERSHIP_EMERGING = "LEADERSHIP_EMERGING"  # early leadership pattern detected
    LEADERSHIP_ABSENT   = "LEADERSHIP_ABSENT"    # behavioral data present but no leadership signals

    # --- Collaboration (M2-7I, DET-12) ---
    COLLABORATION_STRONG    = "COLLABORATION_STRONG"    # strong multi-faceted collaboration pattern
    COLLABORATION_EFFECTIVE = "COLLABORATION_EFFECTIVE" # solid collaboration indicators present
    COLLABORATION_DEFICIT   = "COLLABORATION_DEFICIT"   # individualistic or conflict-avoidant pattern

    # --- Adaptability (M2-7J, DET-13) ---
    ADAPTABILITY_HIGH     = "ADAPTABILITY_HIGH"     # strong recovery and flexibility demonstrated
    ADAPTABILITY_MODERATE = "ADAPTABILITY_MODERATE" # adequate adaptability present
    ADAPTABILITY_LOW      = "ADAPTABILITY_LOW"      # rigidity pattern; low recovery rate

    # --- Confidence Calibration (M2-7K, DET-10) ---
    CONFIDENCE_WELL_CALIBRATED = "CONFIDENCE_WELL_CALIBRATED"  # confidence track is stable and accurate
    CONFIDENCE_OVERCONFIDENT   = "CONFIDENCE_OVERCONFIDENT"    # confidence exceeds actual performance
    CONFIDENCE_UNDERCONFIDENT  = "CONFIDENCE_UNDERCONFIDENT"   # confidence below actual performance
    CONFIDENCE_UNSTABLE        = "CONFIDENCE_UNSTABLE"         # oscillating or erratic confidence track
    CONFIDENCE_SATURATED       = "CONFIDENCE_SATURATED"        # confidence clamped at max/min; no signal
