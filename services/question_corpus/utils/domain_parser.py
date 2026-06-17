# services/question_corpus/utils/domain_parser.py

import logging

from domain.contracts.question.sql_domain import SqlDomain

_logger = logging.getLogger(__name__)

_VALUE_MAP: dict[str, SqlDomain] = {d.value: d for d in SqlDomain}


def parse_sql_domains(value: "str | list | None") -> list[SqlDomain]:
    """Parse domains from any representation into a list of SqlDomain enums.

    Unknown string values fall back to SqlDomain.TECHNICAL_DATABASE with a warning.
    Never raises.
    """
    raw = _to_raw_strings(value)
    result: list[SqlDomain] = []
    for token in raw:
        domain = _VALUE_MAP.get(token)
        if domain is None:
            _logger.warning("Unknown SQL domain %r — falling back to TECHNICAL_DATABASE", token)
            domain = SqlDomain.TECHNICAL_DATABASE
        result.append(domain)
    return result


def parse_domains(value: "str | list | None") -> list[str]:
    """Parse domains from any representation into a clean list of strings.

    Kept for backward-compatibility with callers that still expect list[str].
    Internally delegates to parse_sql_domains and returns .value strings.
    """
    return [d.value for d in parse_sql_domains(value)]


def serialize_domains(value: "str | list | None") -> str:
    """Serialize domains to a CSV string for Chroma metadata storage.

    Accepts list[SqlDomain], list[str], plain str, or None.
    Never raises.
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        tokens: list[str] = []
        for v in value:
            if isinstance(v, SqlDomain):
                tokens.append(v.value)
            else:
                tokens.append(str(v).strip())
        return ",".join(t for t in tokens if t)

    return ""


# ---------------------------------------------------------------------------
# INTERNALS
# ---------------------------------------------------------------------------

def _to_raw_strings(value: "str | list | None") -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        result = []
        for v in value:
            if isinstance(v, SqlDomain):
                result.append(v.value)
            else:
                result.append(str(v).strip())
        return [t for t in result if t]
    return []
