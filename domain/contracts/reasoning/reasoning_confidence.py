# domain/contracts/reasoning/reasoning_confidence.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.data_sufficiency import DataSufficiency


class ReasoningConfidence(BaseModel):
    """Two-tier confidence model for ReasonerDecision (ADR-036).

    reasoning_confidence: how many questions has the Reasoner observed?
      Formula: min(questions_answered / MIN_RELIABLE_EVIDENCE, 1.0)
      where MIN_RELIABLE_EVIDENCE = 3 (implementation detail).

    evidence_strength: how strong are the signals detected this cycle?
      Weighted mean of EvidenceSignal.strength for all new_evidence signals.

    data_sufficiency: derived enum for NarrativeGenerator tone modulation.
      INSUFFICIENT  → hedged language ("limited evidence suggests…")
      TENTATIVE     → qualified language ("early indications show…")
      CONFIDENT     → clear language ("the candidate demonstrates…")
      STRONG        → assertive language ("consistently demonstrates…")
    """

    reasoning_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    data_sufficiency: DataSufficiency = DataSufficiency.INSUFFICIENT

    model_config = {"frozen": True, "extra": "forbid"}
