# domain/contracts/feedback.py

from dataclasses import dataclass
from typing import List, Optional

from domain.contracts.quality import Quality
from domain.contracts.severity import Severity


@dataclass
class FeedbackSignal:
    severity: Severity
    message: str


@dataclass
class LearningSuggestion:
    topic: str
    action: str


@dataclass
class FeedbackBlockResult:
    title: str
    content: str

    severity: Severity
    confidence: float

    signals: List[FeedbackSignal]
    learning: List[LearningSuggestion]

    quality: Optional[Quality] = None
    metadata: Optional[dict] = None


@dataclass
class FeedbackBundle:
    blocks: List[FeedbackBlockResult]

    overall_severity: Severity
    overall_confidence: float
    overall_quality: Quality

    markdown: str
