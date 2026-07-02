# domain/plugins/feature/updaters/reasoning_feature_updater.py

from typing import Any

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_type import ObservationType

_DEEP_TYPES = frozenset({
    ObservationType.REASONING_DEPTH_HIGH,
    ObservationType.REASONING_IMPROVING,
})
_SHALLOW_TYPES = frozenset({
    ObservationType.REASONING_DEPTH_LOW,
    ObservationType.REASONING_STAGNATING,
})
_IDENTITY = FeatureIdentity.for_type(FeatureType.REASONING)


class ReasoningFeatureUpdater(FeatureUpdater):

    @property
    def updater_id(self) -> str:
        return "reasoning_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset({
            ObservationType.REASONING_DEPTH_HIGH.value,
            ObservationType.REASONING_DEPTH_LOW.value,
            ObservationType.REASONING_IMPROVING.value,
            ObservationType.REASONING_STAGNATING.value,
            ObservationType.REASONING_CONTRADICTORY.value,
        })

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset({"reasoning_feature"})

    @property
    def invocation_order(self) -> int:
        return 20

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        typed: list[Observation] = [o for o in observations if isinstance(o, Observation)]
        if not typed:
            return []

        deep_score = sum(o.confidence * o.weight for o in typed if o.observation_type in _DEEP_TYPES)
        shallow_score = sum(o.confidence * o.weight for o in typed if o.observation_type in _SHALLOW_TYPES)
        total = deep_score + shallow_score

        if total == 0.0:
            value = "DEVELOPING"
            ratio = 0.5
        else:
            ratio = deep_score / total
            if ratio >= 0.65:
                value = "DEEP"
            elif ratio <= 0.35:
                value = "SHALLOW"
            else:
                value = "DEVELOPING"

        count = len(typed)
        confidence = min(0.95, 0.4 + 0.08 * count) * (0.5 + 0.5 * abs(ratio - 0.5) * 2)
        confidence = max(0.05, min(1.0, confidence))

        source_ids = tuple(str(o.id) for o in typed)
        question_index = max(o.metadata.question_index for o in typed)

        return [
            FeatureCandidate(
                feature_identity=_IDENTITY,
                candidate_value=value,
                candidate_confidence=confidence,
                source_observation_ids=source_ids,
                computed_at_question_index=question_index,
                updater_id=self.updater_id,
            )
        ]
