# app/ui/presenters/feedback/feedback_models.py

from dataclasses import dataclass
from typing import List, Optional

from app.contracts.feedback_bundle import FeedbackQuality


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

    # quality info
    quality: FeedbackQuality | None = None


# =========================================================
# FINAL BUNDLE
# =========================================================

@dataclass
class FeedbackBundle:
    blocks: List[FeedbackBlockResult]

    # aggregated values
    overall_severity: str
    overall_confidence: float

    # final UI rendering (backward compatibility)
    markdown: str

    # metadata
    metadata: Optional[dict] = None


# =========================================================
# QUALITY
# =========================================================

@dataclass
class FeedbackQuality:
    # "incorrect" | "partial" | "correct" | "optimal" | "inefficient"
    level: str
    explanation: str
