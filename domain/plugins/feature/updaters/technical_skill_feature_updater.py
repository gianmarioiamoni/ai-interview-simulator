# domain/plugins/feature/updaters/technical_skill_feature_updater.py

from typing import Any

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_type import ObservationType

_POSITIVE = frozenset({
    ObservationType.TECHNICAL_CORRECTNESS,
    ObservationType.TECHNICAL_DEPTH,
    ObservationType.TECHNICAL_STRENGTH,
    ObservationType.TECHNICAL_RECOVERED,
})
_NEGATIVE = frozenset({
    ObservationType.TECHNICAL_SHALLOW,
    ObservationType.TECHNICAL_GAP,
})
_IDENTITY = FeatureIdentity.for_type(FeatureType.TECHNICAL_SKILL)


class TechnicalSkillFeatureUpdater(FeatureUpdater):

    @property
    def updater_id(self) -> str:
        return "technical_skill_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset({
            ObservationType.TECHNICAL_CORRECTNESS.value,
            ObservationType.TECHNICAL_DEPTH.value,
            ObservationType.TECHNICAL_SHALLOW.value,
            ObservationType.TECHNICAL_GAP.value,
            ObservationType.TECHNICAL_STRENGTH.value,
            ObservationType.TECHNICAL_RECOVERED.value,
        })

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset({"technical_skill_feature"})

    @property
    def invocation_order(self) -> int:
        return 10

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        typed: list[Observation] = [o for o in observations if isinstance(o, Observation)]
        if not typed:
            return []

        positive_score = sum(o.confidence * o.weight for o in typed if o.observation_type in _POSITIVE)
        negative_score = sum(o.confidence * o.weight for o in typed if o.observation_type in _NEGATIVE)
        total = positive_score + negative_score

        if total == 0.0:
            return []

        ratio = positive_score / total
        if ratio >= 0.65:
            value = "HIGH"
        elif ratio >= 0.40:
            value = "MODERATE"
        else:
            value = "LOW"

        count = len(typed)
        confidence = min(0.95, 0.4 + 0.1 * count) * (0.5 + 0.5 * abs(ratio - 0.5) * 2)
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
