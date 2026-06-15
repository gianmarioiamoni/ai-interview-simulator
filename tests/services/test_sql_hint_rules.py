# tests/services/test_sql_hint_rules.py

import pytest
from services.hint_rules.sql_hint_rules import SQLHintRules


STYLE_QUERY = "SELECT name FROM employees"


# ---------------------------------------------------------
# Style hints suppressed on failure
# ---------------------------------------------------------


def test_no_hints_when_has_failures():
    hints = SQLHintRules.generate(STYLE_QUERY, has_failures=True)
    assert hints == []


def test_no_hints_for_empty_query_on_failure():
    hints = SQLHintRules.generate("", has_failures=True)
    assert hints == []


def test_no_hints_for_empty_query_on_success():
    hints = SQLHintRules.generate("", has_failures=False)
    assert hints == []


# ---------------------------------------------------------
# Style hints emitted on success
# ---------------------------------------------------------


def test_limit_hint_on_success():
    hints = SQLHintRules.generate(STYLE_QUERY, has_failures=False)
    assert any("LIMIT" in h for h in hints)


def test_order_by_hint_on_success():
    hints = SQLHintRules.generate(STYLE_QUERY, has_failures=False)
    assert any("ORDER BY" in h for h in hints)


def test_select_star_hint_on_success():
    hints = SQLHintRules.generate("SELECT * FROM employees", has_failures=False)
    assert any("SELECT *" in h for h in hints)


def test_no_limit_hint_when_limit_present():
    hints = SQLHintRules.generate(
        "SELECT name FROM employees LIMIT 10", has_failures=False
    )
    assert not any("LIMIT" in h for h in hints)


def test_default_has_failures_false():
    """Backward compatibility: default behaviour generates style hints."""
    hints = SQLHintRules.generate(STYLE_QUERY)
    assert len(hints) > 0
