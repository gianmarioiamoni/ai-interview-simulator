# domain/contracts/feature/feature_statistics.py
# FeatureStatistics — aggregate metrics over a FeatureCollection (E01-M4)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_quality import (
    MATURITY_MATURE,
    MATURITY_DEVELOPING,
    MATURITY_NASCENT,
    STABILITY_STABLE,
    STABILITY_UNSTABLE,
    STABILITY_EMERGING,
)


class FeatureStatistics(BaseModel):
    """Aggregate read-only metrics derived from a FeatureCollection.

    Computed once from a snapshot — never stored across cycles.
    FeatureEngine is unchanged; this is a pure runtime layer (E01-M4).
    """

    total_count: int = Field(..., ge=0)
    mean_confidence: float = Field(..., ge=0.0, le=1.0)
    min_confidence: float = Field(..., ge=0.0, le=1.0)
    max_confidence: float = Field(..., ge=0.0, le=1.0)
    low_confidence_count: int = Field(..., ge=0)
    nascent_count: int = Field(..., ge=0)
    developing_count: int = Field(..., ge=0)
    mature_count: int = Field(..., ge=0)
    stable_count: int = Field(..., ge=0)
    unstable_count: int = Field(..., ge=0)
    emerging_count: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_collection(cls, collection: FeatureCollection) -> "FeatureStatistics":
        if collection.is_empty:
            return cls(
                total_count=0,
                mean_confidence=0.0,
                min_confidence=0.0,
                max_confidence=0.0,
                low_confidence_count=0,
                nascent_count=0,
                developing_count=0,
                mature_count=0,
                stable_count=0,
                unstable_count=0,
                emerging_count=0,
            )

        confidences = [f.quality.confidence.value for f in collection.features]
        return cls(
            total_count=collection.size,
            mean_confidence=sum(confidences) / len(confidences),
            min_confidence=min(confidences),
            max_confidence=max(confidences),
            low_confidence_count=sum(1 for c in confidences if c < 0.3),
            nascent_count=sum(
                1 for f in collection.features if f.quality.maturity.stage == MATURITY_NASCENT
            ),
            developing_count=sum(
                1 for f in collection.features if f.quality.maturity.stage == MATURITY_DEVELOPING
            ),
            mature_count=sum(
                1 for f in collection.features if f.quality.maturity.stage == MATURITY_MATURE
            ),
            stable_count=sum(
                1 for f in collection.features if f.quality.stability.state == STABILITY_STABLE
            ),
            unstable_count=sum(
                1 for f in collection.features if f.quality.stability.state == STABILITY_UNSTABLE
            ),
            emerging_count=sum(
                1 for f in collection.features if f.quality.stability.state == STABILITY_EMERGING
            ),
        )

    @property
    def maturity_distribution(self) -> dict[str, int]:
        return {
            MATURITY_NASCENT: self.nascent_count,
            MATURITY_DEVELOPING: self.developing_count,
            MATURITY_MATURE: self.mature_count,
        }

    @property
    def stability_distribution(self) -> dict[str, int]:
        return {
            STABILITY_STABLE: self.stable_count,
            STABILITY_UNSTABLE: self.unstable_count,
            STABILITY_EMERGING: self.emerging_count,
        }
