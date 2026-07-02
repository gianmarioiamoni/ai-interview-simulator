# domain/plugins/feature/updaters/trend_feature_updater.py

from typing import Any

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_type import ObservationType

_IMPROVING = frozenset({
    ObservationType.PERFORMANCE_IMPROVING,
    ObservationType.BEHAVIORAL_GROWTH,
})
_DECLINING = frozenset({ObservationType.PERFORMANCE_DECLINING})
_STABLE = frozenset({ObservationType.PERFORMANCE_STABLE})
_PLATEAU = frozenset({ObservationType.BEHAVIORAL_PLATEAU})
_IDENTITY = FeatureIdentity.for_type(FeatureType.TREND)
_MIN_OBS = 2


class TrendFeatureUpdater(FeatureUpdater):

    @property
    def updater_id(self) -> str:
        return "trend_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset({
            ObservationType.PERFORMANCE_IMPROVING.value,
            ObservationType.PERFORMANCE_DECLINING.value,
            ObservationType.PERFORMANCE_STABLE.value,
            ObservationType.BEHAVIORAL_GROWTH.value,
            ObservationType.BEHAVIORAL_PLATEAU.value,
        })

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset({"trend_feature"})

    @property
    def invocation_order(self) -> int:
        return 50

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        typed: list[Observation] = [o for o in observations if isinstance(o, Observation)]
        if len(typed) < _MIN_OBS:
            return []

        scores: dict[str, float] = {
            "IMPROVING": sum(o.confidence * o.weight for o in typed if o.observation_type in _IMPROVING),
            "DECLINING": sum(o.confidence * o.weight for o in typed if o.observation_type in _DECLINING),
            "STABLE": sum(o.confidence * o.weight for o in typed if o.observation_type in _STABLE),
            "PLATEAU": sum(o.confidence * o.weight for o in typed if o.observation_type in _PLATEAU),
        }

        total = sum(scores.values())
        if total == 0.0:
            return []

        best = max(scores, key=lambda k: scores[k])
        best_ratio = scores[best] / total
        value = best

        count = len(typed)
        confidence = min(0.95, 0.35 + 0.1 * count) * best_ratio
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
