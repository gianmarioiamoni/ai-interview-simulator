# services/question_intelligence/coding_domain_profile.py

from dataclasses import dataclass, field

from domain.contracts.interview.business_context import BusinessContext


@dataclass(frozen=True)
class CodingDomainProfile:
    context_key: BusinessContext
    context_summary: str | None = None
    vocabulary_hint: tuple[str, ...] = field(default_factory=tuple)
    entity_hint: tuple[str, ...] = field(default_factory=tuple)
    scenario_anchor_pool: tuple[str, ...] = field(default_factory=tuple)
    test_scenario_hints: tuple[str, ...] = field(default_factory=tuple)
