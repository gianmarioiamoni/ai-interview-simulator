# services/sql_engine/schema_definition.py

from dataclasses import dataclass, field

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.question.sql_domain import SqlDomain


@dataclass(frozen=True)
class SchemaDefinition:
    context_key: BusinessContext
    schema_sql: str
    seed_sql: str
    domain_tags: tuple[SqlDomain, ...] = field(default_factory=tuple)
    summary_hint: str | None = None
