# domain/contracts/feedback.py

from dataclasses import dataclass
from typing import List, Optional

from domain.contracts.feedback.quality import Quality
from domain.contracts.feedback.severity import Severity


@dataclass
class FeedbackSignal:
    severity: Severity
    message: str


@dataclass
class LearningSuggestion:
    topic: str
    action: str


@dataclass
class FeedbackBlockMetadata:
    score: Optional[int] = None
    passed: Optional[int] = None
    total: Optional[int] = None
    dimension: Optional[str] = None

    def get(self, key: str, default: object = None) -> object:
        return getattr(self, key, default)


@dataclass
class FeedbackBlockResult:
    title: str
    content: str

    severity: Severity
    confidence: float

    signals: List[FeedbackSignal]
    learning: List[LearningSuggestion]

    quality: Optional[Quality] = None
    metadata: Optional[FeedbackBlockMetadata] = None


@dataclass
class FeedbackBundle:
    blocks: List[FeedbackBlockResult]

    overall_severity: Severity
    overall_confidence: float
    overall_quality: Quality

    markdown: str
