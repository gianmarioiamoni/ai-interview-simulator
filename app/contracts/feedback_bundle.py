# app/contracts/feedback_bundle.py

from dataclasses import dataclass
from typing import List, Optional


# =========================================================
# BASIC SIGNALS
# =========================================================

@dataclass
class FeedbackSignal:
    # severity: "info" | "warning" | "error"
    severity: str
    message: str


# =========================================================
# LEARNING SUGGESTIONS
# =========================================================

@dataclass
class LearningSuggestion:
    topic: str
    action: str


# =========================================================
# QUALITY
# =========================================================

@dataclass
class FeedbackQuality:
    # "incorrect" | "partial" | "correct" | "optimal" | "inefficient"
    level: str
    explanation: str


# =========================================================
# BLOCK RESULT
# =========================================================

@dataclass
class FeedbackBlockResult:
    title: str
    content: str

    # semantic info
    severity: str  # "info" | "warning" | "error"
    confidence: float  # 0.0 - 1.0

    # structured signals
    signals: List[FeedbackSignal]
    learning: List[LearningSuggestion]

    # optional quality
    quality: Optional[FeedbackQuality] = None

    # structured metadata
    metadata: Optional[dict] = None


# =========================================================
# FINAL BUNDLE
# =========================================================

@dataclass
class FeedbackBundle:
    blocks: List[FeedbackBlockResult]

    # aggregated values
    overall_severity: str
    overall_confidence: float
    overall_quality: Optional[str]

    # backward compatibility (UI)
    markdown: str
