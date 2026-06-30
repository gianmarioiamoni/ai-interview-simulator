# domain/contracts/reasoning/evidence_polarity.py

from enum import Enum


class EvidencePolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
