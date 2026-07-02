# domain/plugins/feature/updaters/coverage_feature_updater.py

from typing import Any

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_type import ObservationType

_BROAD = frozenset({
    ObservationType.KNOWLEDGE_DEMONSTRATED,
    ObservationType.KNOWLEDGE_CROSS_AREA_CONSISTENT,
})
_NARROW = frozenset({ObservationType.KNOWLEDGE_GAP})
_CONTRADICTORY = frozenset({ObservationType.KNOWLEDGE_CROSS_AREA_CONTRADICTORY})
_IDENTITY = FeatureIdentity.for_type(FeatureType.COVERAGE)
_MIN_OBS = 2


class CoverageFeatureUpdater(FeatureUpdater):

    @property
    def updater_id(self) -> str:
        return "coverage_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset({
            ObservationType.KNOWLEDGE_DEMONSTRATED.value,
            ObservationType.KNOWLEDGE_GAP.value,
            ObservationType.KNOWLEDGE_CROSS_AREA_CONSISTENT.value,
            ObservationType.KNOWLEDGE_CROSS_AREA_CONTRADICTORY.value,
        })

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset({"coverage_feature"})

    @property
    def invocation_order(self) -> int:
        return 40

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        typed: list[Observation] = [o for o in observations if isinstance(o, Observation)]
        if len(typed) < _MIN_OBS:
            return []

        broad_score = sum(o.confidence * o.weight for o in typed if o.observation_type in _BROAD)
        narrow_score = sum(o.confidence * o.weight for o in typed if o.observation_type in _NARROW)
        contra_score = sum(o.confidence * o.weight for o in typed if o.observation_type in _CONTRADICTORY)
        total = broad_score + narrow_score + contra_score

        if total == 0.0:
            value = "UNKNOWN"
            confidence = 0.15
        elif contra_score / total >= 0.4:
            value = "MIXED"
            confidence = min(0.95, 0.3 + 0.08 * len(typed)) * (contra_score / total)
            confidence = max(0.05, min(1.0, confidence))
        else:
            remaining = broad_score + narrow_score
            if remaining == 0.0:
                value = "MIXED"
                ratio = 0.5
            else:
                ratio = broad_score / remaining
                if ratio >= 0.6:
                    value = "BROAD"
                else:
                    value = "NARROW"
            confidence = min(0.95, 0.35 + 0.08 * len(typed)) * (0.5 + 0.5 * abs(ratio - 0.5) * 2)
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
