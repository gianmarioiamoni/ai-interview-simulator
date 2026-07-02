# domain/contracts/feature/feature_batch.py
# FeatureBatch — typed grouping of ProfileFeature by a shared key (E01-M4)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.feature.profile_feature import ProfileFeature


class FeatureBatch(BaseModel):
    """Ordered, homogeneous group of ProfileFeatures sharing a grouping key.

    Produced by grouping operations (e.g. group_by_type, group_by_maturity).
    The key is an opaque string; callers interpret its semantics.

    Invariants:
    - items is never modified after construction (frozen).
    - All items are valid ProfileFeature objects.
    - key must be non-empty.
    """

    key: str = Field(..., min_length=1, description="Grouping key for this batch")
    items: tuple[ProfileFeature, ...] = Field(
        default_factory=tuple,
        description="Ordered ProfileFeatures in this batch",
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def size(self) -> int:
        return len(self.items)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    def feature_type_ids(self) -> frozenset[str]:
        return frozenset(f.feature_identity.feature_type_id for f in self.items)
