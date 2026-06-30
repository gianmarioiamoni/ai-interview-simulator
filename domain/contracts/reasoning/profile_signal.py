# domain/contracts/reasoning/profile_signal.py

from enum import Enum


class ProfileSignal(str, Enum):
    """Observable signals — not scored dimensions.

    Used by PatternDetectors to qualify *why* a dimension score is as it is.
    Never contribute to evaluation scores.
    """
    CONFIDENCE = "confidence"
    CONSISTENCY = "consistency"
    EVIDENCE_QUALITY = "evidence_quality"
    REASONING_DEPTH = "reasoning_depth"
