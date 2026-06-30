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
