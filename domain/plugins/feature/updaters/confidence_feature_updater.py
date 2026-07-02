# domain/plugins/feature/updaters/confidence_feature_updater.py

from typing import Any

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_type import ObservationType

_CALIBRATED = frozenset({ObservationType.CONFIDENCE_WELL_CALIBRATED})
_OVER = frozenset({ObservationType.CONFIDENCE_OVERCONFIDENT})
_UNDER = frozenset({ObservationType.CONFIDENCE_UNDERCONFIDENT})
_UNSTABLE = frozenset({
    ObservationType.CONFIDENCE_UNSTABLE,
    ObservationType.CONFIDENCE_DROP,
    ObservationType.CONFIDENCE_SATURATED,
})
_IDENTITY = FeatureIdentity.for_type(FeatureType.CONFIDENCE)


class ConfidenceFeatureUpdater(FeatureUpdater):

    @property
    def updater_id(self) -> str:
        return "confidence_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset({
            ObservationType.CONFIDENCE_WELL_CALIBRATED.value,
            ObservationType.CONFIDENCE_OVERCONFIDENT.value,
            ObservationType.CONFIDENCE_UNDERCONFIDENT.value,
            ObservationType.CONFIDENCE_UNSTABLE.value,
            ObservationType.CONFIDENCE_SATURATED.value,
            ObservationType.CONFIDENCE_DROP.value,
        })

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset({"confidence_feature"})

    @property
    def invocation_order(self) -> int:
        return 30

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        typed: list[Observation] = [o for o in observations if isinstance(o, Observation)]
        if not typed:
            return []

        scores: dict[str, float] = {
            "CALIBRATED": 0.0,
            "OVERCONFIDENT": 0.0,
            "UNDERCONFIDENT": 0.0,
            "UNSTABLE": 0.0,
        }
        for o in typed:
            w = o.confidence * o.weight
            if o.observation_type in _CALIBRATED:
                scores["CALIBRATED"] += w
            elif o.observation_type in _OVER:
                scores["OVERCONFIDENT"] += w
            elif o.observation_type in _UNDER:
                scores["UNDERCONFIDENT"] += w
            elif o.observation_type in _UNSTABLE:
                scores["UNSTABLE"] += w

        total = sum(scores.values())
        if total == 0.0:
            value = "DEVELOPING"
            confidence = 0.2
        else:
            best = max(scores, key=lambda k: scores[k])
            best_ratio = scores[best] / total
            if best_ratio >= 0.5:
                value = best
            else:
                value = "DEVELOPING"
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
