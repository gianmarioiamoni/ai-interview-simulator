# services/question_corpus/utils/domain_parser.py


def parse_domains(value: "str | list[str] | None") -> list[str]:
    """Parse domains from any representation into a clean list of strings.

    Accepts list, CSV string, or None. Strips whitespace, drops empty tokens.
    Never raises.
    """
    if value is None:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]

    return []


def serialize_domains(value: "str | list[str] | None") -> str:
    """Serialize domains to a CSV string for Chroma metadata storage.

    - list  → comma-joined string
    - str   → returned unchanged (avoids double-serialization)
    - None  → empty string
    Never raises.
    """
    if value is None:
        return ""

    if isinstance(value, list):
        return ",".join(str(v).strip() for v in value if str(v).strip())

    if isinstance(value, str):
        return value

    return ""
